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
    parser.add_argument("--output-prefix", default="predicted")
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


def main() -> None:
    _add_project_root_to_path()
    from evaluation import (
        build_summary_metrics,
        evaluate,
        load_predicted_requirements,
        load_predicted_verdicts,
        load_retrieved_evidence,
        load_true_requirements,
        load_true_verdicts,
    )
    from evaluation.verdict_only import score_verdicts
    from schemas import RetrievedEvidenceRecord

    def find_case_dirs(data_dir: pathlib.Path) -> list[pathlib.Path]:
        case_dirs = []
        for path in sorted(data_dir.iterdir()):
            if not path.is_dir():
                continue
            if not (path / "true_requirements.json").exists():
                continue
            case_dirs.append(path)
        return case_dirs

    def compute_verdict_only_result(case_dir: pathlib.Path):
        verdicts_artifact_path = case_dir / "verdict_only_verdicts.json"
        if not verdicts_artifact_path.exists():
            return None
        verdicts_fixture = load_true_verdicts(
            case_dir / "true_verdicts.json"
        )
        verdict_only_predicted = load_predicted_verdicts(
            verdicts_artifact_path
        )
        retrieved_evidence_path = (
            case_dir / "verdict_only_retrieved_evidence.json"
        )
        retrieved_evidence: list[RetrievedEvidenceRecord] = []
        if retrieved_evidence_path.exists():
            retrieved_evidence = load_retrieved_evidence(
                retrieved_evidence_path
            )
        return score_verdicts(
            verdict_only_predicted, verdicts_fixture, retrieved_evidence
        )

    def metrics_for_case(
        case_dir: pathlib.Path,
        output_prefix: str,
    ) -> dict[str, float | int | None] | None:
        prefix = output_prefix
        predicted_requirements_path = case_dir / f"{prefix}_requirements.json"
        if not predicted_requirements_path.exists():
            return None
        requirements_fixture = load_true_requirements(
            case_dir / "true_requirements.json"
        )
        verdicts_fixture = load_true_verdicts(
            case_dir / "true_verdicts.json"
        )
        predicted_requirements = load_predicted_requirements(
            predicted_requirements_path
        )
        predicted_verdicts = load_predicted_verdicts(
            case_dir / f"{prefix}_verdicts.json"
        )
        retrieved_evidence = load_retrieved_evidence(
            case_dir / f"{prefix}_retrieved_evidence.json"
        )
        report = evaluate(
            requirements_fixture, verdicts_fixture, predicted_requirements,
            predicted_verdicts, retrieved_evidence,
        )
        verdict_only_result = compute_verdict_only_result(case_dir)
        return build_summary_metrics(
            report,
            verdict_only_accuracy=(
                verdict_only_result.accuracy if verdict_only_result
                else None
            ),
            verdict_only_scored=(
                verdict_only_result.scored_topic_count
                if verdict_only_result else None
            ),
        )

    def format_cell(value: float | int | None, key: str) -> str:
        if value is None:
            return "—"
        if key.endswith("_scored") or key.endswith("_count"):
            return str(value)
        return f"{value * 100:.1f}%"

    def mean_row(rows: list[dict[str, float | int | None]]) -> dict[str, str]:
        cells: dict[str, str] = {"case": "**mean**"}
        for key, _label in TABLE_COLUMNS:
            values = [
                row[key] for row in rows
                if isinstance(row.get(key), (int, float))
            ]
            if not values:
                cells[key] = "—"
                continue
            average = sum(values) / len(values)
            cells[key] = f"{average * 100:.1f}% (n={len(values)})"
        return cells

    def render_table(
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
            cells = [format_cell(row.get(key), key) for key, _l in TABLE_COLUMNS]
            lines.append(f"| {case_name} | " + " | ".join(cells) + " |")
        if rows:
            averaged = mean_row(rows)
            cells = [averaged[key] for key, _l in TABLE_COLUMNS]
            lines.append("| **mean** | " + " | ".join(cells) + " |")
        lines.append("")
        return "\n".join(lines)

    arguments = _parse_arguments()
    data_dir = pathlib.Path(arguments.data_dir)
    case_names = []
    rows = []
    skipped = []
    for case_dir in find_case_dirs(data_dir):
        metrics = metrics_for_case(case_dir, arguments.output_prefix)
        if metrics is None:
            skipped.append(case_dir.name)
            continue
        case_names.append(case_dir.name)
        rows.append(metrics)

    table_text = render_table(case_names, rows)
    if skipped:
        table_text += (
            "\nSkipped (no "
            f"`{arguments.output_prefix}_requirements.json` yet): "
            + ", ".join(skipped) + "\n"
        )

    if arguments.output:
        output_path = pathlib.Path(arguments.output)
        output_path.write_text(table_text, encoding="utf-8")
        print(f"Metrics summary written to {output_path}")
    else:
        print(table_text)


if __name__ == "__main__":
    main()
