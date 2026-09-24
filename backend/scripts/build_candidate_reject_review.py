"""Build human-review report for measured current_pass/candidate_reject articles.

Read-only offline script. Reads article_review.jsonl plus optional BART
review set, selects unique measured articles where keyword passed and the
shadow candidate rejected, writes CSV + JSONL triage pack.
"""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from analyze_candidate_shadow import (
    ARTICLE_REVIEW_LOG,
    DEFAULT_REVIEW_SET,
    decision_rows,
    deduplicate_by_url,
    default_classifier,
    match_labels,
    read_jsonl,
)

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = BACKEND_DIR / "logs" / "ingestion" / "review"

CSV_COLUMNS = [
    "title", "provider", "url", "collection_id", "query", "timestamp",
    "keyword_passed", "candidate_passed", "candidate_reason",
    "candidate_matched_terms", "bart_accepted", "bart_score", "bart_label",
    "rejection_reason", "description", "event", "category", "location",
    "human_label", "human_notes", "reviewer_decision", "reviewer_notes",
]

UNAVAILABLE = "not_available_from_logs"


def _matched_terms_text(record: dict) -> str:
    terms = record.get("candidate_matched_terms") or []
    return "; ".join(str(t) for t in terms if str(t))


def _bart_rank(record: dict) -> tuple:
    accepted = record.get("bart_accepted") is True
    score = record.get("bart_score")
    try:
        val = float(score) if score is not None else float("-inf")
    except (TypeError, ValueError):
        val = float("-inf")
    rank_score = -val if val != float("-inf") else float("inf")
    return (0 if accepted else 1, rank_score)
def build_rows(records: list, review_records: list) -> list:
    rows = decision_rows(records, default_classifier())
    unique = deduplicate_by_url(rows)
    subset = [
        r for r in unique
        if r["source"] == "measured"
        and r["current_passed"] is True
        and r["candidate_passed"] is False
    ]
    label_by_key = {}
    for row, label in match_labels(subset, review_records):
        rec = row["record"]
        label_by_key[rec.get("url") or rec.get("title") or ""] = label
    out = []
    for row in subset:
        rec = row["record"]
        label = label_by_key.get(rec.get("url") or rec.get("title") or "", {})
        out.append({
            "title": rec.get("title") or "",
            "provider": rec.get("provider") or "",
            "url": rec.get("url") or "",
            "collection_id": rec.get("collection_id") or "",
            "query": rec.get("query") or "",
            "timestamp": rec.get("timestamp") or "",
            "keyword_passed": True,
            "candidate_passed": False,
            "candidate_reason": row.get("candidate_reason") or "",
            "candidate_matched_terms": list(rec.get("candidate_matched_terms") or []),
            "bart_accepted": rec.get("bart_accepted"),
            "bart_score": rec.get("bart_score"),
            "bart_label": rec.get("bart_label"),
            "rejection_reason": rec.get("rejection_reason"),
            "description": rec.get("description") or "",
            "event": UNAVAILABLE,
            "category": UNAVAILABLE,
            "location": UNAVAILABLE,
            "human_label": label.get("human_label"),
            "human_notes": label.get("notes"),
            "reviewer_decision": "",
            "reviewer_notes": "",
        })
    out.sort(key=lambda i: (
        str(i["candidate_reason"] or ""), _bart_rank(i),
        str(i["provider"] or ""), str(i["title"] or "")))
    return out


def write_outputs(export_rows: list, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "review_current_pass_candidate_reject.csv"
    jsonl_path = out_dir / "review_current_pass_candidate_reject.jsonl"
    with csv_path.open("w", encoding="utf-8", newline="") as s:
        w = csv.DictWriter(s, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for item in export_rows:
            flat = dict(item)
            flat["candidate_matched_terms"] = _matched_terms_text(item)
            w.writerow({c: flat.get(c, "") for c in CSV_COLUMNS})
    with jsonl_path.open("w", encoding="utf-8") as s:
        for item in export_rows:
            s.write(json.dumps(item, ensure_ascii=False) + "\n")
    return csv_path, jsonl_path


def print_summary(export_rows: list) -> None:
    reasons = Counter(str(i["candidate_reason"] or "") for i in export_rows)
    acc = sum(1 for i in export_rows if i["bart_accepted"] is True)
    rej = sum(1 for i in export_rows if i["bart_accepted"] is False)
    print(f"Exported rows: {len(export_rows)}")
    print("Candidate reason breakdown:")
    for reason, count in sorted(reasons.items()):
        print(f"  {reason or '<empty>'}: {count}")
    print(f"BART breakdown: accepted={acc} rejected={rej} missing={len(export_rows)-acc-rej}")


def main() -> None:
    p = argparse.ArgumentParser(description="Export measured pass/reject articles.")
    p.add_argument("--review-log", type=Path, default=ARTICLE_REVIEW_LOG)
    p.add_argument("--review-set", type=Path, default=DEFAULT_REVIEW_SET)
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = p.parse_args()
    records = read_jsonl(args.review_log)
    if not records:
        print(f"No article review records found at {args.review_log}")
        return
    export_rows = build_rows(records, read_jsonl(args.review_set))
    csv_path, jsonl_path = write_outputs(export_rows, args.out_dir)
    print(f"CSV: {csv_path}")
    print(f"JSONL: {jsonl_path}")
    print_summary(export_rows)


if __name__ == "__main__":
    main()

