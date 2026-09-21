import argparse
import pathlib
import sys


def _add_project_root_to_path() -> None:
    project_root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan every case under --data-dir that has been evaluated "
            "and write one combined Markdown table of summary metrics, "
            "plus a mean row, for comparing/averaging across tenders."
        )
    )
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--variant", default="a")
    parser.add_argument("--run-label", default="gemini")
    parser.add_argument("--output")
    return parser.parse_args()


TABLE_COLUMNS = [
    ("requirement_recall", "Recall"),
    ("requirement_precision", "Precision"),
    ("is_mandatory_accuracy", "is_mandatory"),
    ("is_text_verifiable_accuracy", "is_text_verifiable"),
    ("verdict_accuracy", "Verdict acc."),
    ("false_compliant_rate", "False-compliant"),
    ("false_issue_rate", "False-issue"),
    ("evidence_recall", "Evidence recall"),
    ("verdict_only_accuracy", "Verdict-only acc."),
]


def _format_cell(value: float | int | None, key: str) -> str:
    if value is None:
        return "—"
    if key.endswith("_scored") or key.endswith("_count"):
        return str(value)
    return f"{value * 100:.1f}%"


def _mean_row(rows: list[dict[str, float | int | None]]) -> dict[str, str]:
    cells: dict[str, str] = {"case": "**mean**"}
    for key, _label in TABLE_COLUMNS:
        values: list[float | int] = []
        for row in rows:
            value = row.get(key)
            if isinstance(value, (int, float)):
                values.append(value)
        if not values:
            cells[key] = "—"
            continue
        average = sum(values) / len(values)
        cells[key] = f"{average * 100:.1f}% (n={len(values)})"
    return cells


def _render_table(
    case_names: list[str],
    rows: list[dict[str, float | int | None]],
) -> str:
    header = (
        "| Case | " + " | ".join(label for _key, label in TABLE_COLUMNS)
        + " |"
    )
    separator = "|" + "---|" * (len(TABLE_COLUMNS) + 1)
    lines = [
        "# Metrics summary across tenders", "",
        header, separator,
    ]
    for case_name, row in zip(case_names, rows):
        cells = [_format_cell(row.get(key), key) for key, _label in TABLE_COLUMNS]
        lines.append(f"| {case_name} | " + " | ".join(cells) + " |")
    if rows:
        averaged = _mean_row(rows)
        cells = [averaged[key] for key, _label in TABLE_COLUMNS]
        lines.append("| **mean** | " + " | ".join(cells) + " |")
    lines.append("")
    return "\n".join(lines)


def _collect_case_metrics(data_dir: pathlib.Path, variant: str, run_label: str):
    from evaluation.case_metrics import find_case_dirs, metrics_for_case

    case_names = []
    rows = []
    skipped = []
    for case_dir in find_case_dirs(data_dir):
        metrics = metrics_for_case(case_dir, variant, run_label)
        if metrics is None:
            skipped.append(case_dir.name)
            continue
        case_names.append(case_dir.name)
        rows.append(metrics)
    return case_names, rows, skipped


def _write_output(table_text: str, output_arg: str | None) -> None:
    if output_arg:
        output_path = pathlib.Path(output_arg)
        output_path.write_text(table_text, encoding="utf-8")
        print(f"Metrics summary written to {output_path}")
    else:
        print(table_text)


def main() -> None:
    _add_project_root_to_path()
    arguments = _parse_arguments()
    data_dir = pathlib.Path(arguments.data_dir)
    case_names, rows, skipped = _collect_case_metrics(
        data_dir, arguments.variant, arguments.run_label
    )

    table_text = _render_table(case_names, rows)
    if skipped:
        table_text += (
            "\nSkipped (no "
            f"`applications/{arguments.variant}/runs/{arguments.run_label}/"
            "predicted_requirements.json` yet): "
            + ", ".join(skipped) + "\n"
        )
    _write_output(table_text, arguments.output)


if __name__ == "__main__":
    main()
