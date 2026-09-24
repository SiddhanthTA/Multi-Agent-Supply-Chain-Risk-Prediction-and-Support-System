import json
from collections import defaultdict
from pathlib import Path


LOG_DIR = Path(__file__).resolve().parents[1] / "logs" / "ingestion"
METRICS_LOG = LOG_DIR / "metrics.jsonl"
ARTICLE_REVIEW_LOG = LOG_DIR / "article_review.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []

    records = []
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)
    return records


def latest_records(records: list[dict], *, query: str | None = None) -> list[dict]:
    latest = {}
    for record in records:
        if query is not None and record.get("query") != query:
            continue
        key = (record.get("collection_id"), record.get("provider"), record.get("query"))
        latest[key] = record
    return list(latest.values())


def number(records: list[dict], field: str) -> float:
    return sum(float(record.get(field) or 0) for record in records)


def percentage(numerator: float, denominator: float) -> str:
    if not denominator:
        return "0.0%"
    return f"{numerator / denominator * 100:.1f}%"


def print_summary(aggregate_records: list[dict], query_records: list[dict], reviews: list[dict]) -> None:
    print(f"Collection cycles: {len({record.get('collection_id') for record in aggregate_records})}")
    fetched = number(aggregate_records, "raw_fetched")
    keyword_passed = number(aggregate_records, "keyword_passed")
    ai_accepted = number(aggregate_records, "ai_accepted")
    print(f"Articles fetched: {int(fetched)}")
    print(f"Keyword pass rate: {percentage(keyword_passed, fetched)}")
    print(f"BART acceptance rate: {percentage(ai_accepted, keyword_passed)}")
    print(f"Events created: {int(number(aggregate_records, 'events_created'))}")
    duplicates = number(aggregate_records, "duplicate_within_fetch")
    print(f"Duplicate rate: {percentage(duplicates, fetched)}")
    detected = number(aggregate_records, "location_detected")
    unknown = number(aggregate_records, "unknown_location")
    location_total = detected + unknown
    print(f"Location detection rate: {percentage(detected, location_total)}")
    print(f"Unknown location rate: {percentage(unknown, location_total)}")
    print("\nShadow candidate comparison:")
    print(f"Current keyword passed: {int(number(aggregate_records, 'keyword_passed'))}")
    print(f"Current keyword rejected: {int(number(aggregate_records, 'keyword_rejected'))}")
    print(f"Proposed classifier passed: {int(number(aggregate_records, 'proposed_classifier_passed'))}")
    print(f"Proposed classifier rejected: {int(number(aggregate_records, 'proposed_classifier_rejected'))}")
    for field in (
        "current_pass_proposed_pass",
        "current_pass_proposed_reject",
        "current_reject_proposed_pass",
        "current_reject_proposed_reject",
    ):
        print(f"{field}: {int(number(aggregate_records, field))}")

    print("\nPer-query statistics:")
    grouped = defaultdict(list)
    for record in query_records:
        grouped[record.get("query", "<unknown>")].append(record)
    for query, records in grouped.items():
        fetched = number(records, "raw_fetched")
        passed = number(records, "keyword_passed")
        accepted = number(records, "ai_accepted")
        print(
            f"- {query}: fetched={int(fetched)}, "
            f"keyword_pass={percentage(passed, fetched)}, "
            f"bart_accept={percentage(accepted, passed)}, "
            f"duplicates={int(number(records, 'duplicate_within_fetch'))}, "
            f"proposed_pass={int(number(records, 'proposed_classifier_passed'))}, "
            f"proposed_reject={int(number(records, 'proposed_classifier_rejected'))}"
        )

    print("\nPer-provider statistics:")
    grouped = defaultdict(list)
    for record in aggregate_records:
        grouped[record.get("provider", "<unknown>")].append(record)
    for provider, records in grouped.items():
        fetched = number(records, "raw_fetched")
        passed = number(records, "keyword_passed")
        print(
            f"- {provider}: cycles={len(records)}, fetched={int(fetched)}, "
            f"keyword_pass={percentage(passed, fetched)}, "
            f"bart_accept={percentage(number(records, 'ai_accepted'), passed)}, "
            f"events_created={int(number(records, 'events_created'))}"
        )

    # Only articles that cleared the keyword gate reach the AI relevance filter;
    # keyword-rejected rows are logged for candidate-shadow analysis only.
    bart_reviews = [item for item in reviews if item.get("keyword_passed") is not False]

    print("\nReview sample (accepted):")
    for record in [item for item in bart_reviews if item.get("bart_accepted")][:5]:
        print(f"- {record.get('title', '')} [{record.get('provider', '')}]")

    print("\nReview sample (rejected):")
    for record in [item for item in bart_reviews if not item.get("bart_accepted")][:5]:
        reason = record.get("rejection_reason") or "No reason recorded"
        print(f"- {record.get('title', '')} [{reason}]")


def main() -> None:
    metrics = read_jsonl(METRICS_LOG)
    reviews = read_jsonl(ARTICLE_REVIEW_LOG)
    provider_metrics = {
        "NewsAPI",
        "Currents API",
    }
    aggregates = latest_records([
        record for record in metrics
        if record.get("query") == "ALL" and record.get("provider") in provider_metrics
    ])
    queries = latest_records([
        record for record in metrics
        if record.get("query") not in {"ALL", "SCHEDULER"}
        and record.get("provider") in provider_metrics
    ])

    if not metrics:
        print(f"No ingestion metrics found under {LOG_DIR}")
        return

    print_summary(aggregates, queries, reviews)


if __name__ == "__main__":
    main()
