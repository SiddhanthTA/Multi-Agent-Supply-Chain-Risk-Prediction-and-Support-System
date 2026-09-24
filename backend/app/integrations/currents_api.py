import requests

from app.ai.relevance_filter import relevance_filter
from app.ai.candidate_filter import classify_candidate
from app.config.settings import settings
from app.integrations.news_api import is_supply_chain_related
from app.services.ingestion_metrics import (
    base_stats,
    emit_summary,
    finish_stats,
    new_collection_id,
    record_article_review,
    record_candidate_shadow,
    start_timer,
)
from app.utils.logger import logger

CURRENTS_SEARCH_QUERIES = (
    '("supply chain" OR logistics OR procurement OR manufacturing) AND '
    '(disruption OR delay OR shortage OR shutdown OR interruption OR blockage)',
    '(shipping OR freight OR cargo OR vessel OR container OR port OR harbor) AND '
    '(congestion OR closure OR delay OR disruption OR strike OR rerouting OR blockade)',
    '(railway OR rail OR trucking OR truck OR road OR transport OR factory OR infrastructure) AND '
    '(disruption OR closure OR shutdown OR strike OR flood OR cyclone OR earthquake OR storm OR fire)',
    '(tariff OR sanctions OR "export restrictions" OR "import restrictions" OR energy OR refinery OR pipeline OR semiconductor OR supplier) AND '
    '(supply OR trade OR production OR manufacturing OR shipment OR shortage OR disruption)',
)


def _normalize_article(article: dict) -> dict:
    return {
        "title": article.get("title") or "",
        "description": article.get("description") or "",
        "source": "Currents API",
        "published_at": article.get("published"),
        "url": article.get("url"),
    }


def fetch_currents_news(collection_id: str | None = None) -> list | dict:
    """Fetch a bounded set of relevant English articles from Currents API."""
    collection_id = collection_id or new_collection_id()
    aggregate = base_stats(collection_id, "Currents API", "ALL")
    aggregate_started = start_timer()
    if not settings.CURRENTS_API_KEY:
        aggregate["errors"].append("API key is not configured")
        fetch_currents_news.last_stats = aggregate
        emit_summary(logger, finish_stats(aggregate, aggregate_started))
        return {"status": "error", "message": "Currents API key is not configured."}

    headers = {"Authorization": settings.CURRENTS_API_KEY}
    articles = []
    seen_urls = set()

    try:
        for query in CURRENTS_SEARCH_QUERIES:
            query_stats = base_stats(collection_id, "Currents API", query)
            query_started = start_timer()
            query_stats["request_count"] = 1
            aggregate["request_count"] += 1
            response = requests.get(
                settings.CURRENTS_API_BASE_URL,
                headers=headers,
                params={
                    "keywords": query,
                    "language": settings.CURRENTS_LANGUAGE,
                    "page_size": settings.CURRENTS_PAGE_SIZE,
                    "page_number": 1,
                },
                timeout=10,
            )
            response.raise_for_status()
            query_stats["response_status"] = response.status_code
            aggregate["response_status"] = response.status_code
            data = response.json()

            raw_articles = data.get("news", [])
            query_stats["raw_fetched"] = len(raw_articles)
            aggregate["raw_fetched"] += len(raw_articles)

            for raw_article in raw_articles:
                article = _normalize_article(raw_article)
                query_stats["normalized"] += 1
                aggregate["normalized"] += 1
                article_text = f"{article['title']} {article['description']}"

                if not article["url"] or article["url"] in seen_urls:
                    if article["url"] and article["url"] in seen_urls:
                        query_stats["duplicate_within_fetch"] += 1
                        aggregate["duplicate_within_fetch"] += 1
                    continue
                seen_urls.add(article["url"])
                current_passed = is_supply_chain_related(article)
                proposed_result = classify_candidate(article)
                record_candidate_shadow(query_stats, current_passed, proposed_result)
                record_candidate_shadow(aggregate, current_passed, proposed_result)
                if not current_passed:
                    query_stats["keyword_rejected"] += 1
                    aggregate["keyword_rejected"] += 1
                    # Observability only: the keyword gate still decides ingestion,
                    # the candidate decision is logged for offline evaluation.
                    record_article_review(
                        collection_id=collection_id,
                        provider="Currents API",
                        query=query,
                        article=article,
                        keyword_passed=False,
                        candidate_result=proposed_result,
                    )
                    continue
                query_stats["keyword_passed"] += 1
                aggregate["keyword_passed"] += 1

                relevance_result = relevance_filter.evaluate(article_text)
                record_article_review(
                    collection_id=collection_id,
                    provider="Currents API",
                    query=query,
                    article=article,
                    keyword_passed=True,
                    relevance_result=relevance_result,
                    candidate_result=proposed_result,
                )
                if not relevance_result["accepted"]:
                    query_stats["ai_rejected"] += 1
                    aggregate["ai_rejected"] += 1
                    continue

                query_stats["ai_accepted"] += 1
                aggregate["ai_accepted"] += 1
                articles.append(article)

            emit_summary(logger, finish_stats(query_stats, query_started))

        fetch_currents_news.last_stats = aggregate
        emit_summary(logger, finish_stats(aggregate, aggregate_started))
        return articles
    except requests.exceptions.RequestException as exc:
        aggregate["errors"].append(str(exc))
        logger.error("Currents API request failed.")
        fetch_currents_news.last_stats = aggregate
        emit_summary(logger, finish_stats(aggregate, aggregate_started))
        return {"status": "error", "message": "Currents API request failed."}
    except (ValueError, TypeError, KeyError) as exc:
        aggregate["errors"].append(str(exc))
        logger.error("Currents API returned an invalid response.")
        fetch_currents_news.last_stats = aggregate
        emit_summary(logger, finish_stats(aggregate, aggregate_started))
        return {"status": "error", "message": "Currents API returned an invalid response."}
