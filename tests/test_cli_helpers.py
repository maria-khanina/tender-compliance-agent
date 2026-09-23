import pathlib

from cli.aggregate_metrics import _format_cell, _mean_row, _render_table
from cli.evaluate_retrieval import RetrievalRow, _render_retrieval_report
from cli.run_pipeline import _output_paths


def test_format_cell_renders_none_as_em_dash():
    assert _format_cell(None, "requirement_recall") == "—"


def test_format_cell_renders_count_fields_as_plain_integers():
    assert _format_cell(12, "is_mandatory_scored") == "12"
    assert _format_cell(7, "evidence_recall_n_count") == "7"


def test_format_cell_renders_ratio_fields_as_percent():
    assert _format_cell(0.755, "requirement_recall") == "75.5%"


def test_mean_row_averages_only_numeric_values_and_skips_none():
    rows = [
        {"requirement_recall": 0.8, "requirement_precision": None},
        {"requirement_recall": 0.6, "requirement_precision": 0.5},
    ]
    result = _mean_row(rows)
    assert result["requirement_recall"] == "70.0% (n=2)"
    assert result["requirement_precision"] == "50.0% (n=1)"


def test_mean_row_uses_em_dash_when_no_case_has_the_metric():
    rows: list[dict[str, float | int | None]] = [{"requirement_recall": None}]
    result = _mean_row(rows)
    assert result["requirement_recall"] == "—"


def test_render_table_includes_every_case_and_a_mean_row():
    case_names = ["case_a", "case_b"]
    rows: list[dict[str, float | int | None]] = [
        {"requirement_recall": 1.0},
        {"requirement_recall": 0.5},
    ]
    table = _render_table(case_names, rows)
    assert "case_a" in table
    assert "case_b" in table
    assert "**mean**" in table


def test_render_table_empty_rows_has_no_mean_row():
    table = _render_table([], [])
    assert "**mean**" not in table


def test_render_retrieval_report_reports_full_recall():
    rows: list[RetrievalRow] = [{
        "topic_id": "topic_a",
        "gold_evidence_count": 2,
        "found_count": 2,
        "missed_quotes": [],
        "retrieved_chunk_count": 5,
    }]
    report = _render_retrieval_report(rows, total_gold=2, total_found=2)
    assert "100.0%" in report
    assert "none (every gold evidence span was retrieved)" in report


def test_render_retrieval_report_lists_missed_quotes():
    rows: list[RetrievalRow] = [{
        "topic_id": "topic_a",
        "gold_evidence_count": 2,
        "found_count": 1,
        "missed_quotes": ["the missing quote"],
        "retrieved_chunk_count": 3,
    }]
    report = _render_retrieval_report(rows, total_gold=2, total_found=1)
    assert "topic_a" in report
    assert "the missing quote" in report


def test_render_retrieval_report_handles_no_gold_evidence():
    empty_rows: list[RetrievalRow] = []
    report = _render_retrieval_report(empty_rows, total_gold=0, total_found=0)
    assert "No topics with gold evidence to score." in report


def test_output_paths_derive_from_the_report_path_stem():
    output_path = pathlib.Path("data/case/predicted.md")
    requirements_path, verdicts_path, retrieved_context_path = _output_paths(
        output_path
    )
    assert requirements_path == pathlib.Path("data/case/predicted_requirements.json")
    assert verdicts_path == pathlib.Path("data/case/predicted_verdicts.json")
    assert retrieved_context_path == pathlib.Path(
        "data/case/predicted_retrieved_context.json"
    )
