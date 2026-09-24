import json

from scripts.create_bart_review_set import generate_review_set
from scripts.evaluate_bart import print_report, strict_metrics


def write_jsonl(path, records):
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


def review_record(url, accepted, query="query-1", title=None):
    return {
        "provider": "Currents API",
        "query": query,
        "url": url,
        "title": title or url,
        "description": "Description",
        "bart_accepted": accepted,
        "bart_score": 0.8 if accepted else 0.2,
    }


def test_sample_generation_deduplicates_urls_and_keeps_decision_representation(tmp_path):
    source = tmp_path / "article_review.jsonl"
    output = tmp_path / "review.jsonl"
    write_jsonl(source, [
        review_record("https://example.com/a", True, "query-1"),
        review_record("https://example.com/a", False, "query-2"),
        review_record("https://example.com/b", False, "query-2"),
        review_record("https://example.com/c", True, "query-3"),
    ])

    selected = generate_review_set(source, output, sample_size=10)

    assert len(selected) == 3
    assert len({record["url"] for record in selected}) == 3
    assert {record["bart_accepted"] for record in selected} == {True, False}
    assert all(record["human_label"] == "" for record in selected)
    assert all("notes" in record for record in selected)


def test_strict_metrics_exclude_borderline_and_calculate_confusion_matrix():
    records = [
        {"human_label": "relevant", "bart_accepted": True},
        {"human_label": "relevant", "bart_accepted": False},
        {"human_label": "irrelevant", "bart_accepted": True},
        {"human_label": "irrelevant", "bart_accepted": False},
        {"human_label": "borderline", "bart_accepted": True},
        {"human_label": "", "bart_accepted": True},
    ]

    result = strict_metrics(records)

    assert result["total_labeled"] == 5
    assert result["relevant"] == 2
    assert result["borderline"] == 1
    assert result["irrelevant"] == 2
    assert result["bart_accepted"] == 3
    assert result["bart_rejected"] == 2
    assert result["true_positive"] == 1
    assert result["false_positive"] == 1
    assert result["false_negative"] == 1
    assert result["true_negative"] == 1
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5


def test_query_breakdown_and_examples_are_reported(capsys):
    records = [
        {"human_label": "relevant", "bart_accepted": True, "query": "query-1", "title": "Useful"},
        {"human_label": "irrelevant", "bart_accepted": True, "query": "query-1", "title": "False positive"},
        {"human_label": "borderline", "bart_accepted": False, "query": "query-2", "title": "Borderline"},
    ]

    print_report(records)
    output = capsys.readouterr().out

    assert "Per-query statistics:" in output
    assert "False positives:" in output
    assert "False negatives:" in output
    assert "Borderline examples:" in output
    assert "False positive" in output


def test_empty_and_malformed_inputs_are_safe(tmp_path, capsys):
    source = tmp_path / "missing.jsonl"
    output = tmp_path / "review.jsonl"
    assert generate_review_set(source, output, sample_size=5) == []
    assert json.loads(output.read_text(encoding="utf-8").strip() or "null") is None

    malformed = tmp_path / "malformed.jsonl"
    malformed.write_text("not-json\n{}\n", encoding="utf-8")
    selected = generate_review_set(malformed, tmp_path / "malformed-output.jsonl", sample_size=5)
    assert selected == [{
        "review_id": 1,
        "provider": "",
        "query": "",
        "title": "",
        "description": "",
        "url": "",
        "bart_accepted": False,
        "bart_score": None,
        "human_label": "",
        "notes": "",
    }]
