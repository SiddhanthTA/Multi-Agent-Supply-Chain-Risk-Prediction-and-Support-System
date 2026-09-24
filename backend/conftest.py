import pytest

from app.services import ingestion_metrics


@pytest.fixture(autouse=True)
def isolate_ingestion_diagnostics(tmp_path, monkeypatch):
    monkeypatch.setattr(ingestion_metrics, "METRICS_LOG", tmp_path / "metrics.jsonl")
    monkeypatch.setattr(ingestion_metrics, "ARTICLE_REVIEW_LOG", tmp_path / "article_review.jsonl")
