import json

from app.ai.candidate_filter import classify_candidate
from scripts.analyze_candidate_shadow import (
    candidate_decision,
    decision_rows,
    deduplicate_by_url,
    gate_metrics,
    match_labels,
    print_report,
    quadrant_counts,
    read_jsonl,
)


def write_jsonl(path, records):
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


def measured_row(url, keyword_passed, candidate_passed, reason="no_relevant_terms", title=None):
    return {
        "collection_id": "cycle",
        "provider": "NewsAPI",
        "query": "query",
        "url": url,
        "title": title or url,
        "description": "",
        "keyword_passed": keyword_passed,
        "candidate_passed": candidate_passed,
        "candidate_reason": reason,
        "candidate_matched_terms": [],
    }


def reconstructed_row(url, keyword_passed, title, description=""):
    return {
        "collection_id": "cycle",
        "provider": "NewsAPI",
        "query": "query",
        "url": url,
        "title": title,
        "description": description,
        "keyword_passed": keyword_passed,
    }


def test_candidate_decision_prefers_measured_fields():
    record = {"candidate_passed": True, "candidate_reason": "explicit_phrase", "title": "ignored"}
    assert candidate_decision(record, classify_candidate) == (True, "explicit_phrase", "measured")


def test_candidate_decision_reconstructs_when_fields_are_missing():
    record = {"title": "Port closure", "description": "", "keyword_passed": True}
    passed, reason, source = candidate_decision(record, classify_candidate)
    assert passed is True
    assert reason == "explicit_phrase"
    assert source == "reconstructed"


def test_quadrant_counts_include_rescues_and_reasons():
    rows = [
        {"current_passed": True, "candidate_passed": True, "candidate_reason": "domain_event"},
        {"current_passed": True, "candidate_passed": False, "candidate_reason": "generic_domain_only"},
        {"current_passed": False, "candidate_passed": True, "candidate_reason": "strong_event_context"},
        {"current_passed": False, "candidate_passed": False, "candidate_reason": "no_relevant_terms"},
    ]
    counts, reasons = quadrant_counts(rows)
    assert counts["current_pass_candidate_pass"] == 1
    assert counts["current_pass_candidate_reject"] == 1
    assert counts["current_reject_candidate_pass"] == 1
    assert counts["current_reject_candidate_reject"] == 1
    assert reasons["domain_event"] == 1
    assert reasons["strong_event_context"] == 1


def test_gate_metrics_exclude_borderline_and_compute_precision_and_recall():
    labeled = [
        ({"candidate_passed": True}, "relevant"),
        ({"candidate_passed": False}, "relevant"),
        ({"candidate_passed": True}, "irrelevant"),
        ({"candidate_passed": False}, "irrelevant"),
        ({"candidate_passed": True}, "borderline"),
    ]
    metrics = gate_metrics(labeled, "candidate_passed")
    assert metrics["labeled"] == 5
    assert metrics["relevant"] == 2
    assert metrics["irrelevant"] == 2
    assert metrics["borderline"] == 1
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5


def test_match_labels_uses_url_first_then_title():
    rows = [
        {"record": {"url": "https://example.com/a", "title": "Title A"}, "source": "measured"},
        {"record": {"url": "", "title": "Title B"}, "source": "reconstructed"},
        {"record": {"url": "https://example.com/c", "title": "Title C"}, "source": "measured"},
    ]
    review_records = [
        {"url": "https://example.com/a", "title": "Other", "human_label": "relevant"},
        {"url": "", "title": "Title B", "human_label": "irrelevant"},
    ]
    labeled = match_labels(rows, review_records)
    assert [label for _, label in labeled] == ["relevant", "irrelevant"]


def test_deduplicate_by_url_keeps_first_occurrence_and_keeps_blank_urls():
    rows = [
        {"record": {"url": "https://example.com/a"}},
        {"record": {"url": "https://example.com/a"}},
        {"record": {"url": ""}},
        {"record": {"url": ""}},
    ]
    assert len(deduplicate_by_url(rows)) == 3


def test_print_report_separates_measured_from_reconstructed(capsys):
    rows = decision_rows(
        [
            measured_row("https://example.com/m", True, False, "generic_domain_only", "Oil stability"),
            reconstructed_row("https://example.com/r", True, "Port closure"),
        ],
        classify_candidate,
    )

    print_report(rows, [])

    output = capsys.readouterr().out
    assert "measured (candidate fields logged at collection time): 1" in output
    assert "reconstructed (offline re-run of classify_candidate): 1" in output
    assert "Shadow comparison (MEASURED only):" in output
    assert "Shadow comparison (RECONSTRUCTED only):" in output
    assert "No human labels available" in output


def test_print_report_reports_precision_and_recall_when_labels_exist(tmp_path, capsys):
    log_path = tmp_path / "article_review.jsonl"
    review_path = tmp_path / "bart_review_set.jsonl"
    write_jsonl(log_path, [
        measured_row("https://example.com/rel-pass", True, True, "explicit_phrase", "Port closure"),
        measured_row("https://example.com/rel-fail", True, False, "generic_domain_only", "Oil market stability"),
        measured_row("https://example.com/irr-pass", True, True, "domain_event", "Road transport delay"),
        measured_row("https://example.com/irr-fail", True, False, "no_relevant_terms", "Breast pump launch"),
    ])
    write_jsonl(review_path, [
        {"url": "https://example.com/rel-pass", "human_label": "relevant"},
        {"url": "https://example.com/rel-fail", "human_label": "relevant"},
        {"url": "https://example.com/irr-pass", "human_label": "irrelevant"},
        {"url": "https://example.com/irr-fail", "human_label": "irrelevant"},
    ])

    rows = decision_rows(read_jsonl(log_path), classify_candidate)
    print_report(rows, read_jsonl(review_path))

    output = capsys.readouterr().out
    assert "Human-labeled subset: 4 unique articles" in output
    assert "Production keyword gate (is_supply_chain_related):" in output
    assert "Candidate gate (classify_candidate) - MEASURED only:" in output
    # The keyword gate already accepts every logged article, so it has no misses.
    assert "recall=100.0%" in output
    # The candidate gate misses one relevant article here.
    assert "recall=50.0%" in output


def test_main_handles_missing_review_log(tmp_path, monkeypatch, capsys):
    from scripts import analyze_candidate_shadow

    monkeypatch.setattr(
        "sys.argv",
        ["analyze_candidate_shadow", "--review-log", str(tmp_path / "missing.jsonl")],
    )
    analyze_candidate_shadow.main()

    assert "No article review records found" in capsys.readouterr().out


def test_main_runs_on_temp_review_log(tmp_path, monkeypatch, capsys):
    from scripts import analyze_candidate_shadow

    log_path = tmp_path / "article_review.jsonl"
    write_jsonl(log_path, [
        measured_row("https://example.com/a", True, False, "generic_domain_only", "Oil stability"),
    ])
    monkeypatch.setattr(
        "sys.argv",
        [
            "analyze_candidate_shadow",
            "--review-log", str(log_path),
            "--review-set", str(tmp_path / "none.jsonl"),
        ],
    )
    analyze_candidate_shadow.main()

    output = capsys.readouterr().out
    assert "Unique articles by URL: 1" in output
    assert "current_pass_candidate_reject: 1" in output

