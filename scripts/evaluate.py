import argparse
import pathlib
import sys


def _add_project_root_to_path() -> None:
    project_root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate a pipeline run's actual_*.json output against a "
            "case's expected_*.json fixtures."
        )
    )
    parser.add_argument("--case-dir", required=True)
    parser.add_argument("--output-prefix", default="actual")
    parser.add_argument("--report-output")
    return parser.parse_args()


def main() -> None:
    _add_project_root_to_path()
    from evaluation import (
        EvaluationReport,
        ExpectedRequirementsFixture,
        ExpectedVerdictsFixture,
        evaluate,
        load_actual_requirements,
        load_actual_verdicts,
        load_expected_requirements,
        load_expected_verdicts,
        load_retrieved_evidence,
        render_report_as_markdown,
    )
    from schemas import Requirement, RetrievedEvidenceRecord, Verdict

    def load_case_data(
        case_dir: pathlib.Path,
        prefix: str,
    ) -> tuple[
        ExpectedRequirementsFixture,
        ExpectedVerdictsFixture,
        list[Requirement],
        list[Verdict],
        list[RetrievedEvidenceRecord],
    ]:
        requirements_fixture = load_expected_requirements(
            case_dir / "expected_requirements.json"
        )
        verdicts_fixture = load_expected_verdicts(
            case_dir / "expected_verdicts.json"
        )
        actual_requirements = load_actual_requirements(
            case_dir / f"{prefix}_requirements.json"
        )
        actual_verdicts = load_actual_verdicts(
            case_dir / f"{prefix}_verdicts.json"
        )
        retrieved_evidence = load_retrieved_evidence(
            case_dir / f"{prefix}_retrieved_evidence.json"
        )
        return (
            requirements_fixture, verdicts_fixture, actual_requirements,
            actual_verdicts, retrieved_evidence,
        )

    def output_report(
        report_text: str,
        report_output_arg: str | None,
    ) -> None:
        if report_output_arg:
            report_output_path = pathlib.Path(report_output_arg)
            report_output_path.write_text(report_text, encoding="utf-8")
            print(f"Evaluation report written to {report_output_path}")
        else:
            print(report_text)

    arguments = _parse_arguments()
    case_dir = pathlib.Path(arguments.case_dir)
    case_data = load_case_data(case_dir, arguments.output_prefix)
    report: EvaluationReport = evaluate(*case_data)
    report_text = render_report_as_markdown(report)
    output_report(report_text, arguments.report_output)


if __name__ == "__main__":
    main()
