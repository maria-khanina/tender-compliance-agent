import argparse
import pathlib
import sys


def _add_project_root_to_path() -> None:
    project_root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate a pipeline run's predicted_*.json output (under "
            "applications/<variant>/runs/<run-label>/) against a case's "
            "true_*.json fixtures."
        )
    )
    parser.add_argument("--case-dir", required=True)
    parser.add_argument(
        "--variant",
        default="a",
        help=(
            "Application variant directory name under applications/ "
            "(e.g. 'a', 'b', 'c'). Defaults to 'a', the case's canonical "
            "application."
        ),
    )
    parser.add_argument("--run-label", default="gemini")
    parser.add_argument("--report-output")
    return parser.parse_args()


def main() -> None:
    _add_project_root_to_path()
    from evaluation import (
        EvaluationReport,
        TrueRequirementsFixture,
        TrueVerdictsFixture,
        evaluate,
        load_predicted_requirements,
        load_predicted_verdicts,
        load_retrieved_context,
        load_true_requirements,
        load_true_verdicts,
        render_report_as_markdown,
    )
    from evaluation.chunk_diagnostics import describe_missed_topic_chunk_coverage
    from evaluation.span_adapters import group_lookup_by_topic
    from evaluation.unexplained_diagnostics import annotate_unexplained_requirements
    from evaluation.verdict_only import render_verdict_only_report, score_verdicts
    from schemas import Requirement, RetrievedContextRecord, Verdict
    from case_layout import run_dir, true_verdicts_path

    def load_case_data(
        case_dir: pathlib.Path,
        variant: str,
        run_label: str,
    ) -> tuple[
        TrueRequirementsFixture,
        TrueVerdictsFixture,
        list[Requirement],
        list[Verdict],
        list[RetrievedContextRecord],
    ]:
        artifacts_dir = run_dir(case_dir, variant, run_label)
        requirements_fixture = load_true_requirements(
            case_dir / "true_requirements.json"
        )
        verdicts_fixture = load_true_verdicts(
            true_verdicts_path(case_dir, variant)
        )
        predicted_requirements = load_predicted_requirements(
            artifacts_dir / "predicted_requirements.json"
        )
        predicted_verdicts = load_predicted_verdicts(
            artifacts_dir / "predicted_verdicts.json"
        )
        retrieved_context = load_retrieved_context(
            artifacts_dir / "predicted_retrieved_context.json"
        )
        return (
            requirements_fixture, verdicts_fixture, predicted_requirements,
            predicted_verdicts, retrieved_context,
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

    def compute_verdict_only_result(
        case_dir: pathlib.Path, variant: str, run_label: str
    ):
        artifacts_dir = run_dir(case_dir, variant, run_label)
        verdicts_artifact_path = artifacts_dir / "verdict_only_verdicts.json"
        if not verdicts_artifact_path.exists():
            return None
        verdicts_fixture = load_true_verdicts(
            true_verdicts_path(case_dir, variant)
        )
        verdict_only_predicted = load_predicted_verdicts(
            verdicts_artifact_path
        )
        retrieved_context_path = (
            artifacts_dir / "verdict_only_retrieved_context.json"
        )
        retrieved_context: list[RetrievedContextRecord] = []
        if retrieved_context_path.exists():
            retrieved_context = load_retrieved_context(
                retrieved_context_path
            )
        return score_verdicts(
            verdict_only_predicted, verdicts_fixture, retrieved_context
        )

    def compute_missed_chunk_diagnostics(
        requirements_fixture: TrueRequirementsFixture,
        report: EvaluationReport,
    ) -> dict[str, str]:
        topics_by_id = {
            topic.topic_id: topic for topic in requirements_fixture.requirements
        }
        diagnostics = {}
        for topic_id in report.requirement_recall.missed_topic_ids:
            topic = topics_by_id.get(topic_id)
            if topic is None:
                continue
            diagnostics[topic_id] = describe_missed_topic_chunk_coverage(topic)
        return diagnostics

    arguments = _parse_arguments()
    case_dir = pathlib.Path(arguments.case_dir)
    case_data = load_case_data(
        case_dir, arguments.variant, arguments.run_label
    )
    requirements_fixture, _, predicted_requirements, _, _ = case_data
    report: EvaluationReport = evaluate(*case_data)
    verdict_only_result = compute_verdict_only_result(
        case_dir, arguments.variant, arguments.run_label
    )
    missed_chunk_diagnostics = compute_missed_chunk_diagnostics(
        requirements_fixture, report
    )
    unexplained_diagnostics = annotate_unexplained_requirements(
        report.requirement_precision.unexplained_requirement_ids,
        predicted_requirements,
        requirements_fixture,
        group_lookup_by_topic(report.match_groups),
    )
    report_text = render_report_as_markdown(
        report,
        verdict_only_accuracy=(
            verdict_only_result.accuracy if verdict_only_result else None
        ),
        verdict_only_scored=(
            verdict_only_result.scored_topic_count
            if verdict_only_result else None
        ),
        missed_chunk_diagnostics=missed_chunk_diagnostics,
        unexplained_diagnostics=unexplained_diagnostics,
    )
    if verdict_only_result is not None:
        report_text += "\n" + render_verdict_only_report(verdict_only_result)
    output_report(report_text, arguments.report_output)


if __name__ == "__main__":
    main()
