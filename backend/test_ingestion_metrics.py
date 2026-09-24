import json

from app.services import ingestion_metrics


def read_records(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_metrics_append_multiple_cycles_and_review_records_are_written(tmp_path, monkeypatch):
    metrics_path = tmp_path / "metrics.jsonl"
    review_path = tmp_path / "article_review.jsonl"
    monkeypatch.setattr(ingestion_metrics, "METRICS_LOG", metrics_path)
    monkeypatch.setattr(ingestion_metrics, "ARTICLE_REVIEW_LOG", review_path)

    class Logger:
        def info(self, message):
            self.message = message

    logger = Logger()
    ingestion_metrics.emit_summary(logger, {"collection_id": "cycle-1", "query": "ALL"})
    ingestion_metrics.emit_summary(logger, {"collection_id": "cycle-2", "query": "ALL"})
    ingestion_metrics.record_article_review(
        collection_id="cycle-2",
        provider="Currents API",
        query="query",
        article={"url": "https://example.com/a", "title": "Title", "description": "x" * 800},
        keyword_passed=True,
        relevance_result={"accepted": False, "score": 0.3, "reason": "low score"},
    )

    assert [record["collection_id"] for record in read_records(metrics_path)] == ["cycle-1", "cycle-2"]
    review = read_records(review_path)[0]
    assert review["bart_accepted"] is False
    assert len(review["description"]) == 500
    assert review["keyword_passed"] is True


def test_diagnostic_writes_redact_credentials_and_tolerate_optional_fields(tmp_path, monkeypatch):
    metrics_path = tmp_path / "metrics.jsonl"
    review_path = tmp_path / "review.jsonl"
    monkeypatch.setattr(ingestion_metrics, "METRICS_LOG", metrics_path)
    monkeypatch.setattr(ingestion_metrics, "ARTICLE_REVIEW_LOG", review_path)

    class Logger:
        def info(self, message):
            self.message = message

    logger = Logger()
    ingestion_metrics.emit_summary(logger, {
        "collection_id": "cycle",
        "errors": ["api_key=SECRET_VALUE"],
    })
    ingestion_metrics.record_article_review(
        collection_id="cycle",
        provider="Currents API",
        query="query",
        article={"title": None, "description": None},
        keyword_passed=True,
        relevance_result={},
    )

    metrics_text = metrics_path.read_text(encoding="utf-8")
    review_text = review_path.read_text(encoding="utf-8")
    assert "SECRET_VALUE" not in metrics_text
    assert "SECRET_VALUE" not in logger.message
    assert json.loads(review_text)["title"] == ""


def test_analysis_script_handles_empty_log_directory(tmp_path, monkeypatch, capsys):
    from scripts import analyze_ingestion

    monkeypatch.setattr(analyze_ingestion, "LOG_DIR", tmp_path)
    monkeypatch.setattr(analyze_ingestion, "METRICS_LOG", tmp_path / "metrics.jsonl")
    monkeypatch.setattr(analyze_ingestion, "ARTICLE_REVIEW_LOG", tmp_path / "article_review.jsonl")

    analyze_ingestion.main()

    assert "No ingestion metrics found" in capsys.readouterr().out


def test_analysis_script_handles_multiple_cycles(tmp_path, monkeypatch, capsys):
    from scripts import analyze_ingestion

    metrics_path = tmp_path / "metrics.jsonl"
    review_path = tmp_path / "article_review.jsonl"
    records = [
        {"collection_id": "one", "provider": "Currents API", "query": "ALL", "raw_fetched": 10, "keyword_passed": 5, "ai_accepted": 2, "events_created": 2, "duplicate_within_fetch": 1, "location_detected": 1, "unknown_location": 1},
        {"collection_id": "two", "provider": "Currents API", "query": "ALL", "raw_fetched": 20, "keyword_passed": 10, "ai_accepted": 5, "events_created": 5, "duplicate_within_fetch": 2, "location_detected": 4, "unknown_location": 1},
        {"collection_id": "two", "provider": "Currents API", "query": "query-1", "raw_fetched": 10, "keyword_passed": 5, "ai_accepted": 3, "duplicate_within_fetch": 1},
    ]
    metrics_path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
    review_path.write_text("", encoding="utf-8")
    monkeypatch.setattr(analyze_ingestion, "LOG_DIR", tmp_path)
    monkeypatch.setattr(analyze_ingestion, "METRICS_LOG", metrics_path)
    monkeypatch.setattr(analyze_ingestion, "ARTICLE_REVIEW_LOG", review_path)

    analyze_ingestion.main()

    output = capsys.readouterr().out
    assert "Collection cycles: 2" in output
    assert "Articles fetched: 30" in output
    assert "Per-query statistics:" in output


def test_record_article_review_persists_candidate_decision(tmp_path, monkeypatch):
    review_path = tmp_path / "article_review.jsonl"
    monkeypatch.setattr(ingestion_metrics, "ARTICLE_REVIEW_LOG", review_path)

    ingestion_metrics.record_article_review(
        collection_id="cycle",
        provider="NewsAPI",
        query="query",
        article={"url": "https://example.com/a", "title": "Port closure", "description": "terminal"},
        keyword_passed=True,
        relevance_result={"accepted": True, "score": 0.7, "label": "relevant", "reason": "ok"},
        candidate_result={
            "passed": True,
            "reason": "explicit_phrase",
            "matched_terms": ["port closure"],
        },
    )

    review = read_records(review_path)[0]
    assert review["keyword_passed"] is True
    assert review["bart_accepted"] is True
    assert review["candidate_passed"] is True
    assert review["candidate_reason"] == "explicit_phrase"
    assert review["candidate_matched_terms"] == ["port closure"]


def test_record_article_review_logs_keyword_rejected_articles_without_bart(tmp_path, monkeypatch):
    review_path = tmp_path / "article_review.jsonl"
    monkeypatch.setattr(ingestion_metrics, "ARTICLE_REVIEW_LOG", review_path)

    ingestion_metrics.record_article_review(
        collection_id="cycle",
        provider="Currents API",
        query="query",
        article={"url": "https://example.com/b", "title": "shipping", "description": ""},
        keyword_passed=False,
        candidate_result={
            "passed": False,
            "reason": "generic_domain_only",
            "matched_terms": ["shipping"],
        },
    )

    review = read_records(review_path)[0]
    assert review["keyword_passed"] is False
    assert review["candidate_passed"] is False
    assert review["candidate_reason"] == "generic_domain_only"
    assert review["candidate_matched_terms"] == ["shipping"]
    # A keyword-rejected article never reaches BART, so BART fields stay unset.
    assert review["bart_accepted"] is None
    assert review["bart_score"] is None
    assert review["bart_label"] is None
    assert review["rejection_reason"] is None


def test_record_article_review_tolerates_missing_candidate_result(tmp_path, monkeypatch):
    review_path = tmp_path / "article_review.jsonl"
    monkeypatch.setattr(ingestion_metrics, "ARTICLE_REVIEW_LOG", review_path)

    ingestion_metrics.record_article_review(
        collection_id="cycle",
        provider="NewsAPI",
        query="query",
        article={"url": "https://example.com/c", "title": "Title", "description": ""},
        keyword_passed=True,
        relevance_result={"accepted": False},
    )

    review = read_records(review_path)[0]
    assert review["candidate_passed"] is None
    assert review["candidate_reason"] is None
    assert review["candidate_matched_terms"] == []