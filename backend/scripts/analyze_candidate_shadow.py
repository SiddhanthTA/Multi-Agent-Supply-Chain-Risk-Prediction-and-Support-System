"""Offline evaluation of the shadow candidate classifier.

Compares the production keyword gate (``is_supply_chain_related``) with the
shadow candidate classifier (``classify_candidate``) using the per-article
ingestion review log and, where human labels exist, the manual BART review set.

Two evidence grades are always reported separately and never silently mixed:

``measured``
    ``candidate_passed`` / ``candidate_reason`` / ``candidate_matched_terms``
    were written by the ingestion pipeline at collection time.

``reconstructed``
    the review row predates candidate logging, so the decision is reproduced
    offline by re-running ``classify_candidate`` on the stored title and
    description. Reconstructed numbers are indicative, not authoritative.

Precision/recall are only reported for articles that actually carry a human
label in the review set, mirroring ``evaluate_bart`` (borderline rows are
excluded from the strict metrics).
"""

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path

VALID_LABELS = {"relevant", "borderline", "irrelevant"}

BACKEND_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BACKEND_DIR / "logs" / "ingestion"
ARTICLE_REVIEW_LOG = LOG_DIR / "article_review.jsonl"
DEFAULT_REVIEW_SET = LOG_DIR / "review" / "bart_review_set.jsonl"
CANDIDATE_FILTER_PATH = BACKEND_DIR / "app" / "ai" / "candidate_filter.py"

QUADRANTS = (
    "current_pass_candidate_pass",
    "current_pass_candidate_reject",
    "current_reject_candidate_pass",
    "current_reject_candidate_reject",
)

_CLASSIFIER = None


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []

    records = []
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)
    return records


def load_candidate_classifier(path: Path = CANDIDATE_FILTER_PATH):
    """Load ``classify_candidate`` directly from its file.

    Loading by path keeps the script runnable standalone without importing the
    heavier ``app.ai`` package (and its model dependencies).
    """

    spec = importlib.util.spec_from_file_location("candidate_filter", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load candidate classifier from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.classify_candidate


def default_classifier():
    global _CLASSIFIER
    if _CLASSIFIER is None:
        _CLASSIFIER = load_candidate_classifier()
    return _CLASSIFIER


def candidate_decision(record: dict, classify_candidate) -> tuple[bool, str | None, str]:
    """Return ``(passed, reason, source)`` for a single review record."""

    if record.get("candidate_passed") is not None:
        return bool(record.get("candidate_passed")), record.get("candidate_reason"), "measured"

    result = classify_candidate(
        {
            "title": record.get("title") or "",
            "description": record.get("description") or "",
        }
    )
    return bool(result.get("passed")), result.get("reason"), "reconstructed"


def decision_rows(records: list[dict], classify_candidate) -> list[dict]:
    rows = []
    for record in records:
        passed, reason, source = candidate_decision(record, classify_candidate)
        rows.append(
            {
                "record": record,
                "current_passed": record.get("keyword_passed") is True,
                "candidate_passed": passed,
                "candidate_reason": reason,
                "source": source,
            }
        )
    return rows


def deduplicate_by_url(rows: list[dict]) -> list[dict]:
    seen_urls = set()
    unique_rows = []
    for row in rows:
        url = (row["record"].get("url") or "").strip()
        if url:
            if url in seen_urls:
                continue
            seen_urls.add(url)
        unique_rows.append(row)
    return unique_rows


def quadrant_counts(rows: list[dict]) -> tuple[dict, Counter]:
    counts = Counter()
    reasons = Counter()
    for row in rows:
        if row["current_passed"] and row["candidate_passed"]:
            counts["current_pass_candidate_pass"] += 1
        elif row["current_passed"]:
            counts["current_pass_candidate_reject"] += 1
        elif row["candidate_passed"]:
            counts["current_reject_candidate_pass"] += 1
        else:
            counts["current_reject_candidate_reject"] += 1
        if row["candidate_reason"]:
            reasons[row["candidate_reason"]] += 1
    return counts, reasons


def match_labels(rows: list[dict], review_records: list[dict]) -> list[tuple[dict, str]]:
    """Attach human labels to review rows by URL, then by title."""

    by_url = {}
    by_title = {}
    for record in review_records:
        url = (record.get("url") or "").strip()
        if url:
            by_url.setdefault(url, record)
        title = (record.get("title") or "").strip()
        if title:
            by_title.setdefault(title, record)

    labeled = []
    for row in rows:
        record = row["record"]
        url = (record.get("url") or "").strip()
        title = (record.get("title") or "").strip()
        human = by_url.get(url) if url else None
        if human is None and title:
            human = by_title.get(title)
        if human is None:
            continue
        label = human.get("human_label")
        if label in VALID_LABELS:
            labeled.append((row, label))
    return labeled


def gate_metrics(labeled: list[tuple[dict, str]], decision_key: str) -> dict:
    """Strict precision/recall for one gate over human-labeled rows."""

    relevant = [(row, label) for row, label in labeled if label == "relevant"]
    irrelevant = [(row, label) for row, label in labeled if label == "irrelevant"]

    true_positive = sum(1 for row, _ in relevant if row[decision_key])
    false_negative = sum(1 for row, _ in relevant if not row[decision_key])
    false_positive = sum(1 for row, _ in irrelevant if row[decision_key])
    true_negative = sum(1 for row, _ in irrelevant if not row[decision_key])

    return {
        "labeled": len(labeled),
        "relevant": len(relevant),
        "irrelevant": len(irrelevant),
        "borderline": sum(1 for _, label in labeled if label == "borderline"),
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "true_negative": true_negative,
        "precision": (
            true_positive / (true_positive + false_positive)
            if true_positive + false_positive
            else None
        ),
        "recall": (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative
            else None
        ),
    }


def format_rate(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def print_gate_metrics(title: str, metrics: dict) -> None:
    print(
        f"  {title}: labeled={metrics['labeled']}, relevant={metrics['relevant']}, "
        f"irrelevant={metrics['irrelevant']}"
    )
    print(
        f"    precision={format_rate(metrics['precision'])} "
        f"recall={format_rate(metrics['recall'])} "
        f"tp={metrics['true_positive']} fp={metrics['false_positive']} "
        f"fn={metrics['false_negative']} tn={metrics['true_negative']}"
    )


def print_shadow_comparison(title: str, rows: list[dict]) -> None:
    counts, reasons = quadrant_counts(rows)
    current_passed = counts["current_pass_candidate_pass"] + counts["current_pass_candidate_reject"]
    current_rejected = counts["current_reject_candidate_pass"] + counts["current_reject_candidate_reject"]
    candidate_passed = counts["current_pass_candidate_pass"] + counts["current_reject_candidate_pass"]
    candidate_rejected = counts["current_pass_candidate_reject"] + counts["current_reject_candidate_reject"]

    print(f"\n{title}:")
    print(f"  Articles: {len(rows)}")
    print(f"  Current keyword gate passed: {current_passed}")
    print(f"  Current keyword gate rejected: {current_rejected}")
    print(f"  Candidate gate passed: {candidate_passed}")
    print(f"  Candidate gate rejected: {candidate_rejected}")
    for quadrant in QUADRANTS:
        print(f"  {quadrant}: {counts[quadrant]}")
    if reasons:
        reason_text = ", ".join(f"{reason}={count}" for reason, count in sorted(reasons.items()))
        print(f"  Candidate reason counts: {reason_text}")


def print_report(rows: list[dict], review_records: list[dict]) -> None:
    unique_rows = deduplicate_by_url(rows)
    measured = [row for row in unique_rows if row["source"] == "measured"]
    reconstructed = [row for row in unique_rows if row["source"] == "reconstructed"]

    print(f"Review rows read: {len(rows)}")
    print(f"Unique articles by URL: {len(unique_rows)}")
    print("\nEvidence quality:")
    print(f"  measured (candidate fields logged at collection time): {len(measured)}")
    print(f"  reconstructed (offline re-run of classify_candidate): {len(reconstructed)}")

    print_shadow_comparison("Shadow comparison (all unique articles)", unique_rows)
    print_shadow_comparison("Shadow comparison (MEASURED only)", measured)
    print_shadow_comparison("Shadow comparison (RECONSTRUCTED only)", reconstructed)

    labeled = match_labels(unique_rows, review_records)
    print(f"\nHuman-labeled subset: {len(labeled)} unique articles matched to the review set")
    if not labeled:
        print("  No human labels available; precision/recall cannot be measured.")
        return

    measured_labeled = [(row, label) for row, label in labeled if row["source"] == "measured"]
    reconstructed_labeled = [(row, label) for row, label in labeled if row["source"] == "reconstructed"]

    print("  (strict metrics exclude borderline rows)")
    print("\nProduction keyword gate (is_supply_chain_related):")
    print_gate_metrics("all labeled", gate_metrics(labeled, "current_passed"))
    print("\nCandidate gate (classify_candidate) - MEASURED only:")
    print_gate_metrics("measured labeled", gate_metrics(measured_labeled, "candidate_passed"))
    print("\nCandidate gate (classify_candidate) - RECONSTRUCTED only:")
    print_gate_metrics("reconstructed labeled", gate_metrics(reconstructed_labeled, "candidate_passed"))
    print("\nCandidate gate (classify_candidate) - measured + reconstructed:")
    print_gate_metrics("all labeled", gate_metrics(labeled, "candidate_passed"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate the shadow candidate classifier against the production keyword gate."
    )
    parser.add_argument("--review-log", type=Path, default=ARTICLE_REVIEW_LOG)
    parser.add_argument("--review-set", type=Path, default=DEFAULT_REVIEW_SET)
    args = parser.parse_args()

    records = read_jsonl(args.review_log)
    if not records:
        print(f"No article review records found at {args.review_log}")
        return

    review_records = read_jsonl(args.review_set)
    rows = decision_rows(records, default_classifier())
    print_report(rows, review_records)


if __name__ == "__main__":
    main()
