import argparse
from collections import defaultdict
from pathlib import Path
import json

VALID_LABELS = {"relevant", "borderline", "irrelevant"}
DEFAULT_INPUT = Path(__file__).resolve().parents[1] / "logs" / "ingestion" / "review" / "bart_review_set.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def strict_metrics(records: list[dict]) -> dict:
    labeled = [record for record in records if record.get("human_label") in VALID_LABELS]
    strict = [record for record in labeled if record.get("human_label") != "borderline"]
    relevant = [record for record in strict if record.get("human_label") == "relevant"]
    irrelevant = [record for record in strict if record.get("human_label") == "irrelevant"]

    true_positive = sum(record in relevant and record.get("bart_accepted") is True for record in strict)
    false_positive = sum(record in irrelevant and record.get("bart_accepted") is True for record in strict)
    false_negative = sum(record in relevant and record.get("bart_accepted") is False for record in strict)
    true_negative = sum(record in irrelevant and record.get("bart_accepted") is False for record in strict)
    return {
        "total_labeled": len(labeled),
        "relevant": len(relevant),
        "borderline": sum(record.get("human_label") == "borderline" for record in labeled),
        "irrelevant": len(irrelevant),
        "bart_accepted": sum(record.get("bart_accepted") is True for record in labeled),
        "bart_rejected": sum(record.get("bart_accepted") is False for record in labeled),
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "true_negative": true_negative,
        "precision": true_positive / (true_positive + false_positive) if true_positive + false_positive else None,
        "recall": true_positive / (true_positive + false_negative) if true_positive + false_negative else None,
    }


def format_rate(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def query_label(query: str) -> str:
    return "NewsAPI" if not query.startswith("(") else query


def print_examples(records: list[dict], accepted: bool, human_label: str, title: str) -> None:
    print(f"\n{title}:")
    examples = [
        record for record in records
        if record.get("bart_accepted") is accepted and record.get("human_label") == human_label
    ]
    if not examples:
        print("- None")
    for record in examples[:5]:
        print(
            f"- {record.get('title', '')} | query={query_label(record.get('query', ''))} | "
            f"BART={'accepted' if record.get('bart_accepted') else 'rejected'} | human={human_label}"
        )


def print_report(records: list[dict]) -> None:
    metrics = strict_metrics(records)
    print(f"Total labeled articles: {metrics['total_labeled']}")
    print(f"Relevant: {metrics['relevant']}")
    print(f"Borderline: {metrics['borderline']}")
    print(f"Irrelevant: {metrics['irrelevant']}")
    print(f"BART accepted: {metrics['bart_accepted']}")
    print(f"BART rejected: {metrics['bart_rejected']}")
    print("\nStrict evaluation excludes borderline rows.")
    print(f"False positives: {metrics['false_positive']}")
    print(f"False negatives: {metrics['false_negative']}")
    print(f"Precision: {format_rate(metrics['precision'])}")
    print(f"Recall: {format_rate(metrics['recall'])}")
    print("\nConfusion matrix (strict labels):")
    print("                 Human relevant  Human irrelevant")
    print(f"BART accepted    {metrics['true_positive']:15}  {metrics['false_positive']:17}")
    print(f"BART rejected    {metrics['false_negative']:15}  {metrics['true_negative']:17}")

    print("\nPer-query statistics:")
    groups = defaultdict(list)
    for record in records:
        groups[query_label(record.get("query", ""))].append(record)
    for query, group in groups.items():
        result = strict_metrics(group)
        print(
            f"- {query}: labeled={result['total_labeled']}, relevant={result['relevant']}, "
            f"borderline={result['borderline']}, irrelevant={result['irrelevant']}, "
            f"accepted={result['bart_accepted']}, rejected={result['bart_rejected']}, "
            f"precision={format_rate(result['precision'])}, recall={format_rate(result['recall'])}"
        )

    print_examples(records, True, "irrelevant", "False positives")
    print_examples(records, False, "relevant", "False negatives")
    print("\nBorderline examples:")
    borderline = [record for record in records if record.get("human_label") == "borderline"]
    for record in borderline[:5]:
        print(
            f"- {record.get('title', '')} | query={query_label(record.get('query', ''))} | "
            f"BART={'accepted' if record.get('bart_accepted') else 'rejected'} | human=borderline"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate manually labeled BART review records.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()
    records = read_jsonl(args.input)
    if not records:
        print(f"No review records found at {args.input}")
        return
    print_report(records)


if __name__ == "__main__":
    main()
