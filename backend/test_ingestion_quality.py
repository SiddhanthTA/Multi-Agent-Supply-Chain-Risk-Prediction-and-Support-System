from unittest.mock import MagicMock, patch

import requests

from app.crud.event import save_normalized_event
from app.integrations.currents_api import CURRENTS_SEARCH_QUERIES, fetch_currents_news
from app.integrations.news_api import (
    _due_targeted_query,
    configured_news_targeted_search_queries,
    fetch_supply_chain_news,
    is_supply_chain_related,
    reset_targeted_query_state,
)
from app.models.event import Event
from app.schemas.event import EventCreate
from app.services.event_service import store_news_events
from app.services.ingestion_metrics import base_stats


def currents_response(articles, status_code=200):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = {"news": articles}
    response.raise_for_status.return_value = None
    return response


def news_response(articles, status_code=200):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = {"articles": articles}
    response.raise_for_status.return_value = None
    return response


def accepted_currents_article(url):
    return {
        "title": "Port disruption delays vessel cargo",
        "description": "A shipping disruption affects freight supply.",
        "url": url,
        "published": "2026-09-23T08:00:00Z",
    }


def accepted_news_article(url):
    return {
        "title": "Port disruption delays cargo",
        "description": "A shipping disruption affects freight supply.",
        "source": {"name": "Example News"},
        "publishedAt": "2026-09-23T08:00:00Z",
        "url": url,
    }


def test_currents_uses_four_non_location_queries_and_deduplicates_urls():
    duplicate = accepted_currents_article("https://example.com/duplicate")
    payloads = [currents_response([duplicate]) for _ in CURRENTS_SEARCH_QUERIES]

    with patch("app.integrations.currents_api.settings.CURRENTS_API_KEY", "configured"), \
         patch("app.integrations.currents_api.relevance_filter.evaluate", return_value={"accepted": True}), \
            patch("app.integrations.currents_api.emit_summary") as emit_summary, \
         patch("app.integrations.currents_api.requests.get", side_effect=payloads) as request:
        articles = fetch_currents_news(collection_id="test-cycle")

    assert len(CURRENTS_SEARCH_QUERIES) == 4
    assert request.call_count == 4
    assert len(articles) == 1
    assert all("dubai" not in query.lower() for query in CURRENTS_SEARCH_QUERIES)
    assert all("singapore" not in query.lower() for query in CURRENTS_SEARCH_QUERIES)
    assert all("rotterdam" not in query.lower() for query in CURRENTS_SEARCH_QUERIES)
    aggregate = emit_summary.call_args_list[-1].args[1]
    assert aggregate["duplicate_within_fetch"] == 3


def test_keyword_filter_covers_new_vocabulary_but_rejects_irrelevant_articles():
    for term in (
        "disruption", "delay", "congestion", "closure", "shutdown", "shortage",
        "vessel", "trucking", "railway", "tariff", "refinery", "labor",
        "sanctions", "export restrictions", "import restrictions", "rerouting",
        "blockade", "blackout",
    ):
        assert is_supply_chain_related({"title": term, "description": ""})

    assert not is_supply_chain_related({
        "title": "Celebrity announces a new album",
        "description": "Entertainment news and interviews.",
    })


def test_targeted_news_queries_rotate_once_per_six_hour_window():
    with patch("app.integrations.news_api.settings.NEWS_TARGETED_QUERIES_ENABLED", True), \
         patch("app.integrations.news_api.settings.NEWS_TARGETED_QUERY_INTERVAL_MINUTES", 360):
        queries = configured_news_targeted_search_queries()
        assert [location for location, _ in queries] == [
            "India",
            "United States",
            "Singapore",
        ]
        reset_targeted_query_state()
        assert _due_targeted_query(0) == queries[0]
        assert _due_targeted_query(60) is None
        assert _due_targeted_query((6 * 60 * 60) - 1) is None
        assert _due_targeted_query(6 * 60 * 60) == queries[1]
        assert _due_targeted_query((12 * 60 * 60) - 1) is None
        assert _due_targeted_query(12 * 60 * 60) == queries[2]
        assert _due_targeted_query((18 * 60 * 60) - 1) is None
        assert _due_targeted_query(18 * 60 * 60) == queries[0]

    reset_targeted_query_state()


def test_newsapi_combines_global_and_due_targeted_results_through_existing_filters():
    global_article = accepted_news_article("https://example.com/global")
    targeted_article = {
        **accepted_news_article("https://example.com/india"),
        "title": "India oil imports disrupted by shipping delay",
        "description": "India faces a fuel supply disruption.",
    }
    responses = [
        news_response([global_article]),
        news_response([targeted_article]),
    ]

    queries = configured_news_targeted_search_queries()
    with patch("app.integrations.news_api.settings.NEWS_API_KEY", "configured"), \
         patch("app.integrations.news_api.settings.NEWS_SEARCH_QUERY", "global-query"), \
         patch("app.integrations.news_api.settings.NEWS_TARGETED_QUERIES_ENABLED", True), \
         patch("app.integrations.news_api.settings.NEWS_TARGETED_QUERY_INTERVAL_MINUTES", 360), \
         patch("app.integrations.news_api.time.time", return_value=0), \
         patch("app.integrations.news_api.relevance_filter.evaluate", return_value={
             "accepted": True, "score": 0.9, "label": "relevant", "reason": "test"
         }), \
         patch("app.integrations.news_api.record_article_review") as record_review, \
         patch("app.integrations.news_api.requests.get", side_effect=responses) as request:
        reset_targeted_query_state()
        articles = fetch_supply_chain_news(collection_id="targeted-cycle")

    reset_targeted_query_state()
    assert request.call_count == 2
    assert request.call_args_list[0].kwargs["params"]["q"] == "global-query"
    assert request.call_args_list[1].kwargs["params"]["q"] == queries[0][1]
    assert [article["url"] for article in articles] == [
        "https://example.com/global",
        "https://example.com/india",
    ]
    assert articles[0]["targeted_location"] is None
    assert articles[1]["targeted_location"] == "India"
    assert fetch_supply_chain_news.last_stats["request_count"] == 2
    assert fetch_supply_chain_news.last_stats["targeted_request_count"] == 1
    assert fetch_supply_chain_news.last_stats["targeted_queries"] == ["India"]
    assert fetch_supply_chain_news.last_stats["targeted_raw_fetched"] == 1
    query_metrics = {
        item["query"]: item
        for item in fetch_supply_chain_news.last_stats["query_metrics"]
    }
    assert query_metrics[queries[0][1]]["targeted_location"] == "India"
    assert query_metrics[queries[0][1]]["raw_fetched"] == 1
    assert query_metrics[queries[0][1]]["keyword_passed"] == 1
    assert query_metrics[queries[0][1]]["ai_accepted"] == 1
    assert query_metrics["global-query"]["targeted_location"] is None
    assert {call.kwargs["query"] for call in record_review.call_args_list} == {
        "global-query",
        queries[0][1],
    }


def test_targeted_newsapi_429_is_isolated_recorded_and_not_retried():
    global_article = accepted_news_article("https://example.com/global-before-429")
    rate_limited = MagicMock(status_code=429)
    error = requests.exceptions.HTTPError("429 Client Error", response=rate_limited)
    queries = configured_news_targeted_search_queries()

    with patch("app.integrations.news_api.settings.NEWS_API_KEY", "configured"), \
         patch("app.integrations.news_api.settings.NEWS_SEARCH_QUERY", "global-query"), \
         patch("app.integrations.news_api.settings.NEWS_TARGETED_QUERIES_ENABLED", True), \
         patch("app.integrations.news_api.settings.NEWS_TARGETED_QUERY_INTERVAL_MINUTES", 360), \
         patch("app.integrations.news_api.time.time", return_value=0), \
         patch("app.integrations.news_api.relevance_filter.evaluate", return_value={
             "accepted": True, "score": 0.9, "label": "relevant", "reason": "test"
         }), \
         patch("app.integrations.news_api.requests.get", side_effect=[
             news_response([global_article]),
             error,
         ]) as request:
        reset_targeted_query_state()
        articles = fetch_supply_chain_news(collection_id="targeted-429-cycle")
        assert _due_targeted_query((6 * 60 * 60) - 1) is None
        assert _due_targeted_query(6 * 60 * 60) == queries[1]

    reset_targeted_query_state()
    assert request.call_count == 2
    assert request.call_args_list[0].kwargs["params"]["q"] == "global-query"
    assert request.call_args_list[1].kwargs["params"]["q"] == queries[0][1]
    assert [article["url"] for article in articles] == [global_article["url"]]
    assert fetch_supply_chain_news.last_stats["request_count"] == 2
    assert fetch_supply_chain_news.last_stats["targeted_request_count"] == 1
    assert fetch_supply_chain_news.last_stats["targeted_raw_fetched"] == 0
    assert any("HTTP 429" in error for error in fetch_supply_chain_news.last_stats["errors"])
    query_metrics = {
        item["query"]: item
        for item in fetch_supply_chain_news.last_stats["query_metrics"]
    }
    targeted_metrics = query_metrics[queries[0][1]]
    assert targeted_metrics["targeted_location"] == "India"
    assert targeted_metrics["response_status"] == 429
    assert targeted_metrics["raw_fetched"] == 0
    assert any("HTTP 429" in error for error in targeted_metrics["errors"])


def test_newsapi_targeted_failure_does_not_discard_global_results():
    global_article = accepted_news_article("https://example.com/global-only")
    responses = [news_response([global_article]), requests.exceptions.Timeout("target timeout")]

    with patch("app.integrations.news_api.settings.NEWS_API_KEY", "configured"), \
         patch("app.integrations.news_api.settings.NEWS_SEARCH_QUERY", "global-query"), \
         patch("app.integrations.news_api.settings.NEWS_TARGETED_QUERIES_ENABLED", True), \
         patch("app.integrations.news_api.settings.NEWS_TARGETED_QUERY_INTERVAL_MINUTES", 360), \
         patch("app.integrations.news_api.time.time", return_value=0), \
         patch("app.integrations.news_api.relevance_filter.evaluate", return_value={
             "accepted": True, "score": 0.9, "label": "relevant", "reason": "test"
         }), \
         patch("app.integrations.news_api.requests.get", side_effect=responses) as request:
        reset_targeted_query_state()
        articles = fetch_supply_chain_news(collection_id="targeted-failure-cycle")

    reset_targeted_query_state()
    assert request.call_count == 2
    assert [article["url"] for article in articles] == ["https://example.com/global-only"]
    assert fetch_supply_chain_news.last_stats["targeted_request_count"] == 1
    assert fetch_supply_chain_news.last_stats["targeted_queries"] == ["India"]
    assert fetch_supply_chain_news.last_stats["errors"]


def test_candidate_classifier_remains_shadow_only_for_targeted_results():
    article = {
        **accepted_news_article("https://example.com/candidate-shadow"),
        "title": "India port congestion delays cargo",
    }

    with patch("app.integrations.news_api.settings.NEWS_API_KEY", "configured"), \
         patch("app.integrations.news_api.settings.NEWS_TARGETED_QUERIES_ENABLED", False), \
         patch("app.integrations.news_api.relevance_filter.evaluate", return_value={
             "accepted": True, "score": 0.8, "label": "relevant", "reason": "test"
         }), \
         patch("app.integrations.news_api.classify_candidate", return_value={
             "passed": False, "reason": "generic_domain_only", "matched_terms": ["port"]
         }) as candidate, \
         patch("app.integrations.news_api.record_article_review") as record_review, \
         patch("app.integrations.news_api.requests.get", return_value=news_response([article])):
        articles = fetch_supply_chain_news(collection_id="candidate-shadow-cycle")

    candidate.assert_called_once_with(article)
    assert [item["url"] for item in articles] == ["https://example.com/candidate-shadow"]
    review = record_review.call_args.kwargs
    assert review["keyword_passed"] is True
    assert review["relevance_result"]["accepted"] is True
    assert review["candidate_result"]["passed"] is False


def test_newsapi_deduplicates_accepted_urls_within_one_fetch():
    article = accepted_news_article("https://example.com/news-duplicate")
    with patch("app.integrations.news_api.settings.NEWS_API_KEY", "configured"), \
         patch("app.integrations.news_api.settings.NEWS_TARGETED_QUERIES_ENABLED", False), \
         patch("app.integrations.news_api.relevance_filter.evaluate", return_value={
             "accepted": True, "score": 0.9, "label": "relevant", "reason": "test"
         }), \
         patch("app.integrations.news_api.requests.get", return_value=news_response([article, article])):
        articles = fetch_supply_chain_news(collection_id="test-news-cycle")

    assert len(articles) == 1


def test_newsapi_deduplicates_same_url_across_global_and_targeted_results():
    duplicate = accepted_news_article("https://example.com/cross-query-duplicate")
    targeted = {
        **duplicate,
        "title": "India port congestion delays cargo",
    }
    queries = configured_news_targeted_search_queries()

    with patch("app.integrations.news_api.settings.NEWS_API_KEY", "configured"), \
         patch("app.integrations.news_api.settings.NEWS_SEARCH_QUERY", "global-query"), \
         patch("app.integrations.news_api.settings.NEWS_TARGETED_QUERIES_ENABLED", True), \
         patch("app.integrations.news_api.settings.NEWS_TARGETED_QUERY_INTERVAL_MINUTES", 360), \
         patch("app.integrations.news_api.time.time", return_value=0), \
         patch("app.integrations.news_api.relevance_filter.evaluate", return_value={
             "accepted": True, "score": 0.9, "label": "relevant", "reason": "test"
         }), \
         patch("app.integrations.news_api.requests.get", side_effect=[
             news_response([duplicate]),
             news_response([targeted]),
         ]) as request:
        reset_targeted_query_state()
        articles = fetch_supply_chain_news(collection_id="cross-query-cycle")

    reset_targeted_query_state()
    assert request.call_count == 2
    assert [article["url"] for article in articles] == [duplicate["url"]]
    assert fetch_supply_chain_news.last_stats["duplicate_within_fetch"] == 1
    query_metrics = {
        item["query"]: item
        for item in fetch_supply_chain_news.last_stats["query_metrics"]
    }
    assert query_metrics[queries[0][1]]["duplicate_within_fetch"] == 1


def test_location_resolver_controls_stored_event_location():
    article = accepted_currents_article("https://example.com/location-authority")
    saved_event = MagicMock(id=7)
    db = MagicMock()
    db.query.return_value.all.return_value = []
    db.query.return_value.filter.return_value.first.return_value = None

    with patch("app.services.event_service.fetch_supply_chain_news", return_value=[]), \
         patch("app.services.event_service.fetch_currents_news", return_value=[article]), \
         patch("app.services.event_service.resolve_event_location", return_value={"primary_location": "Singapore"}), \
         patch("app.services.event_service.save_normalized_event", return_value=saved_event) as save_event, \
         patch("app.services.event_service.process_event"):
        store_news_events(db, collection_id="location-cycle")

    assert save_event.call_args.args[1]["location"] == "Singapore"


def test_store_news_events_attributes_created_event_to_targeted_query_metrics():
    target_query = configured_news_targeted_search_queries()[0][1]
    article = {
        **accepted_currents_article("https://example.com/targeted-persistence"),
        "source": "Example News",
        "published_at": "2026-09-23T08:00:00Z",
        "collection_query": target_query,
        "targeted_location": "India",
    }
    query_metrics = base_stats("targeted-persistence-cycle", "NewsAPI", target_query)
    query_metrics["targeted_location"] = "India"
    news_stats = base_stats("targeted-persistence-cycle", "NewsAPI", target_query)
    news_stats["query_metrics"] = [query_metrics]
    saved_event = MagicMock(id=8)
    db = MagicMock()
    db.query.return_value.all.return_value = []
    db.query.return_value.filter.return_value.first.return_value = None
    news_fetcher = MagicMock(return_value=[article])
    news_fetcher.last_stats = news_stats
    currents_fetcher = MagicMock(return_value=[])
    currents_fetcher.last_stats = base_stats(
        "targeted-persistence-cycle", "Currents API", "ALL"
    )

    with patch("app.services.event_service.fetch_supply_chain_news", news_fetcher), \
         patch("app.services.event_service.fetch_currents_news", currents_fetcher), \
         patch("app.services.event_service.resolve_event_location", return_value={
             "primary_location": "India"
         }), \
         patch("app.services.event_service.save_normalized_event", return_value=saved_event), \
         patch("app.services.event_service.process_event"):
        store_news_events(db, collection_id="targeted-persistence-cycle")

    assert query_metrics["events_created"] == 1
    assert query_metrics["events_skipped"] == 0


def test_currents_failure_returns_safe_error_and_logs_request_metrics():
    with patch("app.integrations.currents_api.settings.CURRENTS_API_KEY", "configured"), \
         patch("app.integrations.currents_api.emit_summary") as emit_summary, \
         patch("app.integrations.currents_api.requests.get", side_effect=requests.exceptions.Timeout("secret network detail")):
        result = fetch_currents_news(collection_id="failure-cycle")

    assert result["status"] == "error"
    assert "secret network detail" not in result["message"]
    assert emit_summary.call_args.args[1]["provider"] == "Currents API"
    assert emit_summary.call_args.args[1]["request_count"] == 1
    assert emit_summary.call_args.args[1]["errors"]


def test_database_url_deduplication_still_returns_existing_event():
    db = MagicMock()
    existing = Event(id=11, title="Existing", event_type="News", url="https://example.com/db-dedup")
    db.query.return_value.filter.return_value.first.return_value = existing

    event_data = EventCreate(
        title="Duplicate",
        event_type="News",
        source="Currents API",
        source_type="news",
        url="https://example.com/db-dedup",
    ).model_dump()

    assert save_normalized_event(db, event_data) is existing
    db.add.assert_not_called()