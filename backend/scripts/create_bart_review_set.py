import argparse
import json
from collections import defaultdict, deque
from pathlib import Path

DEFAULT_INPUT = Path(__file__).resolve().parents[1] / "logs" / "ingestion" / "article_review.jsonl"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "logs" / "ingestion" / "review" / "bart_review_set.jsonl"


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


def deduplicate(records: list[dict]) -> list[dict]:
    result = []
    seen_urls = set()
    for record in records:
        url = (record.get("url") or "").strip()
        if url:
            if url in seen_urls:
                continue
            seen_urls.add(url)
        result.append(record)
    return result


def sample_records(records: list[dict], sample_size: int) -> list[dict]:
    unique_records = deduplicate(records)
    strata = defaultdict(deque)
    for record in sorted(unique_records, key=lambda item: (item.get("timestamp") or "", item.get("url") or "")):
        if record.get("keyword_passed") is False:
            # Keyword-rejected articles never reach the AI relevance filter, so
            # they are excluded from the BART review set.
            continue
        provider = record.get("provider") or "Unknown provider"
        query = record.get("query") or "Unknown query"
        decision = "accepted" if record.get("bart_accepted") else "rejected"
        strata[(provider, query, decision)].append(record)

    selected = []
    while strata and len(selected) < sample_size:
        for key in list(strata):
            bucket = strata[key]
            if bucket:
                selected.append(bucket.popleft())
                if len(selected) >= sample_size:
                    break
            if not bucket:
                del strata[key]

    return selected


def to_review_record(record: dict, review_id: int) -> dict:
    return {
        "review_id": review_id,
        "provider": record.get("provider") or "",
        "query": record.get("query") or "",
        "title": record.get("title") or "",
        "description": record.get("description") or "",
        "url": record.get("url") or "",
        "bart_accepted": bool(record.get("bart_accepted")),
        "bart_score": record.get("bart_score"),
        "human_label": "",
        "notes": "",
    }


def generate_review_set(input_path: Path, output_path: Path, sample_size: int = 40) -> list[dict]:
    selected = sample_records(read_jsonl(input_path), sample_size)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as stream:
        for index, record in enumerate(selected, start=1):
            stream.write(json.dumps(to_review_record(record, index), ensure_ascii=False) + "\n")
    return [to_review_record(record, index) for index, record in enumerate(selected, start=1)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a manually labeled BART review set.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--sample-size", type=int, default=40)
    args = parser.parse_args()

    records = generate_review_set(args.input, args.output, max(0, args.sample_size))
    accepted = sum(record["bart_accepted"] for record in records)
    print(f"Selected: {len(records)}")
    print(f"Accepted: {accepted}")
    print(f"Rejected: {len(records) - accepted}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
