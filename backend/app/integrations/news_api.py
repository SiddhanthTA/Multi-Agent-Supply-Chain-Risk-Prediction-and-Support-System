import time

import requests

from app.config.settings import settings
from app.utils.logger import logger
from app.ai.relevance_filter import relevance_filter
from app.ai.candidate_filter import classify_candidate
from app.services.ingestion_metrics import (
    base_stats,
    emit_summary,
    finish_stats,
    new_collection_id,
    record_article_review,
    record_candidate_shadow,
    start_timer,
)

# --------------------------------------------------
# SUPPLY CHAIN KEYWORDS
# --------------------------------------------------

SUPPLY_CHAIN_KEYWORDS = [
    "supply chain",
    "logistics",
    "shipping",
    "ship",
    "freight",
    "cargo",
    "warehouse",
    "transport",
    "transportation",
    "port",
    "harbor",
    "terminal",
    "container",
    "customs",
    "import",
    "export",
    "supplier",
    "procurement",
    "manufacturing",
    "factory",
    "production",
    "distribution",
    "inventory",
    "rail",
    "truck",
    "road",
    "air freight",
    "sea freight",
    "semiconductor",
    "oil",
    "gas",
    "energy",
    "pipeline",
    "strike",
    "disruption",
    "delay",
    "congestion",
    "closure",
    "shutdown",
    "shortage",
    "vessel",
    "trucking",
    "railway",
    "tariff",
    "refinery",
    "labor",
    "sanctions",
    "export restrictions",
    "import restrictions",
    "rerouting",
    "blockade",
    "blackout",
    "flood",
    "earthquake",
    "cyclone",
    "hurricane",
    "storm",
]

# --------------------------------------------------
# CHECK ARTICLE RELEVANCE (Keyword Filter)
# --------------------------------------------------


def is_supply_chain_related(article: dict) -> bool:
    """
    Check whether a news article is related to supply chain
    using the fast keyword filter.
    """

    text = (
        f"{article.get('title', '')} "
        f"{article.get('description', '')}"
    ).lower()

    return any(
        keyword in text
        for keyword in SUPPLY_CHAIN_KEYWORDS
    )


# Query location and text are configured in Settings/.env. The integration only
# validates the rotation order and maps each location to its configured query.
NEWS_TARGETED_LOCATION_QUERY_SETTINGS = {
    "India": "NEWS_TARGETED_QUERY_INDIA",
    "United States": "NEWS_TARGETED_QUERY_UNITED_STATES",
    "Singapore": "NEWS_TARGETED_QUERY_SINGAPORE",
}


def configured_news_targeted_search_queries() -> tuple[tuple[str, str], ...]:
    queries = []
    for item in settings.NEWS_TARGETED_LOCATION_ROTATION.split(","):
        location = item.strip()
        setting_name = NEWS_TARGETED_LOCATION_QUERY_SETTINGS.get(location)
        if setting_name and location not in {name for name, _ in queries}:
            queries.append((location, str(getattr(settings, setting_name)).strip()))
    return tuple(queries)


_targeted_query_state = {
    "next_due_at": None,
    "next_index": 0,
}


def reset_targeted_query_state() -> None:
    """Reset the in-process six-hour rotation (primarily useful for tests)."""
    _targeted_query_state["next_due_at"] = None
    _targeted_query_state["next_index"] = 0


def _due_targeted_query(now: float | None = None) -> tuple[str, str] | None:
    if not settings.NEWS_TARGETED_QUERIES_ENABLED:
        return None

    queries = configured_news_targeted_search_queries()
    if not queries:
        return None

    current_time = time.time() if now is None else now
    interval_seconds = max(int(settings.NEWS_TARGETED_QUERY_INTERVAL_MINUTES), 1) * 60
    next_due_at = _targeted_query_state["next_due_at"]
    if next_due_at is not None and current_time < next_due_at:
        return None

    index = _targeted_query_state["next_index"] % len(queries)
    _targeted_query_state["next_due_at"] = current_time + interval_seconds
    _targeted_query_state["next_index"] = index + 1
    return queries[index]


def _request_newsapi_articles(query: str, page_size: int) -> tuple[int, list[dict]]:
    response = requests.get(
        settings.NEWS_API_BASE_URL,
        params={
            "q": query,
            "language": settings.NEWS_LANGUAGE,
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "apiKey": settings.NEWS_API_KEY,
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    articles = data.get("articles", [])
    return response.status_code, articles if isinstance(articles, list) else []


# --------------------------------------------------
# FETCH NEWS
# --------------------------------------------------


def fetch_supply_chain_news(collection_id: str | None = None):
    """
    Fetch supply chain related news from NewsAPI.

    Pipeline:
        NewsAPI
            ↓
        Keyword Filter
            ↓
        AI Relevance Filter
            ↓
        Final Articles
    """

    collection_id = collection_id or new_collection_id()
    stats = base_stats(collection_id, "NewsAPI", settings.NEWS_SEARCH_QUERY)
    global_query_stats = base_stats(collection_id, "NewsAPI", settings.NEWS_SEARCH_QUERY)
    global_query_stats["targeted_location"] = None
    global_query_stats["request_count"] = 1
    stats["query_metrics"] = [global_query_stats]
    stats["targeted_request_count"] = 0
    stats["targeted_queries"] = []
    stats["targeted_raw_fetched"] = 0
    started = start_timer()

    try:
        logger.info("=" * 60)
        logger.info("Starting NewsAPI collection pipeline")
        logger.info("=" * 60)

        logger.info("Requesting latest global supply-chain news from NewsAPI...")
        response_status, global_articles = _request_newsapi_articles(
            settings.NEWS_SEARCH_QUERY,
            settings.NEWS_PAGE_SIZE,
        )
        stats["request_count"] = 1
        stats["response_status"] = response_status
        global_query_stats["response_status"] = response_status
        global_query_stats["raw_fetched"] = len(global_articles)
        global_query_stats["normalized"] = len(global_articles)

        article_batches = [(settings.NEWS_SEARCH_QUERY, global_articles, None)]
        targeted = _due_targeted_query()
        if targeted is not None:
            location_name, targeted_query = targeted
            logger.info(
                f"Requesting supplemental NewsAPI coverage for {location_name}..."
            )
            targeted_query_stats = base_stats(collection_id, "NewsAPI", targeted_query)
            targeted_query_stats["targeted_location"] = location_name
            targeted_query_stats["request_count"] = 1
            stats["query_metrics"].append(targeted_query_stats)
            stats["request_count"] += 1
            stats["targeted_request_count"] += 1
            stats["targeted_queries"].append(location_name)
            try:
                targeted_status, targeted_articles = _request_newsapi_articles(
                    targeted_query,
                    settings.NEWS_TARGETED_PAGE_SIZE,
                )
                targeted_query_stats["response_status"] = targeted_status
                article_batches.append((targeted_query, targeted_articles, location_name))
                targeted_query_stats["raw_fetched"] = len(targeted_articles)
                targeted_query_stats["normalized"] = len(targeted_articles)
                stats["targeted_raw_fetched"] += len(targeted_articles)
            except requests.exceptions.HTTPError as exc:
                response = exc.response
                status_code = response.status_code if response is not None else None
                if status_code == 429:
                    # Targeted collection is supplemental: record the quota
                    # failure, return no targeted articles, and never retry.
                    targeted_query_stats["response_status"] = 429
                    error_message = (
                        f"Targeted NewsAPI request rate limited for {location_name} "
                        "(HTTP 429); global results retained"
                    )
                    stats["errors"].append(error_message)
                    targeted_query_stats["errors"].append(error_message)
                    logger.warning(error_message)
                else:
                    error_message = (
                        f"Targeted NewsAPI request failed for {location_name}: {exc}"
                    )
                    stats["errors"].append(error_message)
                    targeted_query_stats["errors"].append(error_message)
                    logger.warning(
                        f"Targeted NewsAPI request failed for {location_name}; "
                        "continuing with global results."
                    )
            except (
                requests.exceptions.RequestException,
                TypeError,
                ValueError,
                AttributeError,
            ) as exc:
                # The global collection is still useful if the optional
                # quota-saving location request fails.
                error_message = (
                    f"Targeted NewsAPI request failed for {location_name}: {exc}"
                )
                stats["errors"].append(error_message)
                targeted_query_stats["errors"].append(error_message)
                logger.warning(
                    f"Targeted NewsAPI request failed for {location_name}; "
                    "continuing with global results."
                )

        fetched_articles = [
            (query, article, targeted_location)
            for query, batch, targeted_location in article_batches
            for article in batch
            if isinstance(article, dict)
        ]

        # --------------------------------------------------
        # INITIAL STATISTICS
        # --------------------------------------------------

        total_articles = len(fetched_articles)
        stats["raw_fetched"] = total_articles
        stats["normalized"] = total_articles

        keyword_passed = 0
        keyword_rejected = 0
        articles = []

        ai_accepted = 0
        ai_rejected = 0
        seen_urls = set()

        logger.info(
            f"Total Articles Received: {total_articles}"
        )

        # --------------------------------------------------
        # PROCESS ARTICLES
        # --------------------------------------------------

        for article_query, article, targeted_location in fetched_articles:
            query_stats = next(
                (
                    item
                    for item in stats["query_metrics"]
                    if item.get("query") == article_query
                ),
                stats,
            )

            title = article.get("title", "")
            description = article.get("description", "")

            article_text = f"{title} {description}"

            # --------------------------------------------------
            # STEP 1: KEYWORD FILTER
            # --------------------------------------------------

            current_passed = is_supply_chain_related(article)
            proposed_result = classify_candidate(article)
            record_candidate_shadow(stats, current_passed, proposed_result)
            record_candidate_shadow(query_stats, current_passed, proposed_result)

            if not current_passed:

                keyword_rejected += 1
                stats["keyword_rejected"] += 1
                query_stats["keyword_rejected"] += 1

                logger.info(
                    f"[KEYWORD FILTER] Rejected | "
                    f"Title={title}"
                )

                # Observability only: the production keyword gate above decides
                # ingestion, while the candidate decision is recorded so the
                # offline evaluation can see articles the candidate would rescue.
                record_article_review(
                    collection_id=collection_id,
                    provider="NewsAPI",
                    query=article_query,
                    article=article,
                    keyword_passed=False,
                    candidate_result=proposed_result,
                )

                continue

            keyword_passed += 1
            stats["keyword_passed"] += 1
            query_stats["keyword_passed"] += 1

            logger.info(
                f"[KEYWORD FILTER] Passed | "
                f"Title={title}"
            )

            # --------------------------------------------------
            # STEP 2: AI RELEVANCE FILTER
            # --------------------------------------------------

            relevance_result = relevance_filter.evaluate(
                article_text
            )

            record_article_review(
                collection_id=collection_id,
                provider="NewsAPI",
                query=article_query,
                article=article,
                keyword_passed=True,
                relevance_result=relevance_result,
                candidate_result=proposed_result,
            )

            ai_score = relevance_result["score"]
            ai_label = relevance_result["label"]
            ai_reason = relevance_result["reason"]

            if not relevance_result["accepted"]:

                ai_rejected += 1
                stats["ai_rejected"] += 1
                query_stats["ai_rejected"] += 1

                logger.info(
                    f"[AI FILTER] Rejected | "
                    f"Score={ai_score:.4f} | "
                    f"Label={ai_label} | "
                    f"Reason={ai_reason} | "
                    f"Title={title}"
                )

                continue

            ai_accepted += 1
            stats["ai_accepted"] += 1
            query_stats["ai_accepted"] += 1

            article_url = article.get("url")
            if article_url and article_url in seen_urls:
                stats["duplicate_within_fetch"] += 1
                query_stats["duplicate_within_fetch"] += 1
                continue
            if article_url:
                seen_urls.add(article_url)

            logger.info(
                f"[AI FILTER] Accepted | "
                f"Score={ai_score:.4f} | "
                f"Label={ai_label} | "
                f"Title={title}"
            )

            # --------------------------------------------------
            # FINAL ACCEPTED ARTICLE
            # --------------------------------------------------

            articles.append(
                {
                    "title": title,
                    "description": description,
                    "source": article.get(
                        "source", {}
                    ).get("name"),
                    "published_at": article.get(
                        "publishedAt"
                    ),
                    "url": article.get("url"),
                    "collection_query": article_query,
                    "targeted_location": targeted_location,
                }
            )

            logger.info(
                f"[FINAL] Article Accepted: {title}"
            )

        # --------------------------------------------------
        # CALCULATE STATISTICS
        # --------------------------------------------------

        keyword_pass_rate = (
            (keyword_passed / total_articles) * 100
            if total_articles > 0
            else 0
        )

        ai_acceptance_rate = (
            (ai_accepted / keyword_passed) * 100
            if keyword_passed > 0
            else 0
        )

        final_acceptance_rate = (
            (len(articles) / total_articles) * 100
            if total_articles > 0
            else 0
        )

        # --------------------------------------------------
        # FINAL SUMMARY
        # --------------------------------------------------

        logger.info("=" * 60)
        logger.info("NEWS FILTER SUMMARY")
        logger.info("=" * 60)

        logger.info(
            f"Total Articles Received : {total_articles}"
        )

        logger.info("")
        logger.info("KEYWORD FILTER")
        logger.info(
            f"  Passed                : {keyword_passed}"
        )
        logger.info(
            f"  Rejected              : {keyword_rejected}"
        )
        logger.info(
            f"  Pass Rate             : "
            f"{keyword_pass_rate:.2f}%"
        )

        logger.info("")
        logger.info("AI RELEVANCE FILTER")
        logger.info(
            f"  Accepted              : {ai_accepted}"
        )
        logger.info(
            f"  Rejected              : {ai_rejected}"
        )
        logger.info(
            f"  Acceptance Rate       : "
            f"{ai_acceptance_rate:.2f}%"
        )

        logger.info("")
        logger.info(
            f"FINAL ARTICLES         : {len(articles)}"
        )
        logger.info(
            f"FINAL ACCEPTANCE RATE  : "
            f"{final_acceptance_rate:.2f}%"
        )

        logger.info("=" * 60)

        fetch_supply_chain_news.last_stats = stats
        emit_summary(logger, finish_stats(stats, started))

        return articles

    except requests.exceptions.RequestException as e:

        stats["errors"].append(str(e))
        fetch_supply_chain_news.last_stats = stats
        emit_summary(logger, finish_stats(stats, started))

        logger.error(
            f"NewsAPI request failed: {str(e)}"
        )

        return {
            "status": "error",
            "message": str(e),
        }