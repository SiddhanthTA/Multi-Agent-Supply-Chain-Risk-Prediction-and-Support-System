from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time
import uuid

LOG_DIR = Path(__file__).resolve().parents[2] / "logs" / "ingestion"
METRICS_LOG = LOG_DIR / "metrics.jsonl"
ARTICLE_REVIEW_LOG = LOG_DIR / "article_review.jsonl"
MAX_DESCRIPTION_LENGTH = 500
SENSITIVE_VALUE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|password|passwd|secret|token)(\s*[:=]\s*)([^\s,;&]+)"
)


def new_collection_id() -> str:
    return uuid.uuid4().hex[:12]


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def start_timer() -> float:
    return time.perf_counter()


def emit_summary(logger, fields: dict) -> None:
    record = _sanitize(fields)
    record.setdefault("timestamp", utc_timestamp())
    logger.info(
        "[INGESTION] "
        + json.dumps(record, default=str, separators=(",", ":"), sort_keys=True)
    )
    _append_jsonl(METRICS_LOG, record)


def _candidate_fields(candidate_result: dict | None) -> dict:
    """Normalize the shadow candidate classifier decision for review logging.

    ``None`` means the article never reached the candidate shadow evaluation,
    which is different from an evaluated article that the classifier rejected.
    """

    if not isinstance(candidate_result, dict):
        return {
            "candidate_passed": None,
            "candidate_reason": None,
            "candidate_matched_terms": [],
        }

    matched_terms = candidate_result.get("matched_terms")
    if not isinstance(matched_terms, (list, tuple)):
        matched_terms = []

    return {
        "candidate_passed": bool(candidate_result.get("passed")),
        "candidate_reason": candidate_result.get("reason"),
        "candidate_matched_terms": [str(term) for term in matched_terms],
    }


def record_article_review(
    *,
    collection_id: str,
    provider: str,
    query: str,
    article: dict,
    keyword_passed: bool,
    relevance_result: dict | None = None,
    candidate_result: dict | None = None,
) -> None:
    if isinstance(relevance_result, dict):
        bart_accepted = bool(relevance_result.get("accepted", False))
        bart_score = relevance_result.get("score")
        bart_label = relevance_result.get("label")
        rejection_reason = relevance_result.get("reason")
    else:
        # Articles that stop at the keyword or candidate gate never reach BART.
        bart_accepted = None
        bart_score = None
        bart_label = None
        rejection_reason = None

    record = {
        "collection_id": collection_id,
        "provider": provider,
        "query": query,
        "url": article.get("url"),
        "title": article.get("title") or "",
        "description": (article.get("description") or "")[:MAX_DESCRIPTION_LENGTH],
        "keyword_passed": keyword_passed,
        "bart_accepted": bart_accepted,
        "bart_score": bart_score,
        "bart_label": bart_label,
        "rejection_reason": rejection_reason,
        **_candidate_fields(candidate_result),
        "timestamp": utc_timestamp(),
    }
    _append_jsonl(ARTICLE_REVIEW_LOG, record)


def _append_jsonl(path: Path, record: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(_sanitize(record), default=str, separators=(",", ":")) + "\n")
    except OSError:
        # Diagnostics must never interrupt ingestion.
        return


def _sanitize(value):
    if isinstance(value, dict):
        return {key: _sanitize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, str):
        return SENSITIVE_VALUE_PATTERN.sub(r"\1\2[REDACTED]", value)
    return value


def base_stats(collection_id: str, provider: str, query: str) -> dict:
    return {
        "collection_id": collection_id,
        "started_at": utc_timestamp(),
        "completed_at": None,
        "provider": provider,
        "query": query,
        "request_count": 0,
        "response_status": None,
        "raw_fetched": 0,
        "normalized": 0,
        "keyword_rejected": 0,
        "keyword_passed": 0,
        "proposed_classifier_passed": 0,
        "proposed_classifier_rejected": 0,
        "current_pass_proposed_pass": 0,
        "current_pass_proposed_reject": 0,
        "current_reject_proposed_pass": 0,
        "current_reject_proposed_reject": 0,
        "proposed_reason_counts": {},
        "ai_rejected": 0,
        "ai_accepted": 0,
        "duplicate_within_fetch": 0,
        "duplicate_existing_event": 0,
        "location_detected": 0,
        "unknown_location": 0,
        "events_created": 0,
        "events_skipped": 0,
        "errors": [],
        "duration_ms": 0,
    }


def record_candidate_shadow(stats: dict, current_passed: bool, proposed_result: dict) -> None:
    proposed_passed = bool(proposed_result.get("passed"))
    reason = proposed_result.get("reason") or "unknown"
    if proposed_passed:
        stats["proposed_classifier_passed"] += 1
    else:
        stats["proposed_classifier_rejected"] += 1
    stats["proposed_reason_counts"][reason] = (
        stats["proposed_reason_counts"].get(reason, 0) + 1
    )

    comparison_key = (
        "current_pass_proposed_pass" if current_passed and proposed_passed else
        "current_pass_proposed_reject" if current_passed else
        "current_reject_proposed_pass" if proposed_passed else
        "current_reject_proposed_reject"
    )
    stats[comparison_key] += 1


def finish_stats(stats: dict, started: float) -> dict:
    stats["completed_at"] = utc_timestamp()
    stats["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
    return stats
