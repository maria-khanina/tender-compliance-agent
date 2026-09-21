"""Computes one case's summary metrics, shared by the CLI scripts that
aggregate or record metrics across cases."""
import pathlib

from evaluation import (
    build_summary_metrics,
    evaluate,
    load_predicted_requirements,
    load_predicted_verdicts,
    load_retrieved_context,
    load_true_requirements,
    load_true_verdicts,
)
from evaluation.verdict_only import score_verdicts
from schemas import RetrievedContextRecord
from case_layout import run_dir, true_verdicts_path


def find_case_dirs(data_dir: pathlib.Path) -> list[pathlib.Path]:
    case_dirs = []
    for path in sorted(data_dir.iterdir()):
        if not path.is_dir():
            continue
        if not (path / "true_requirements.json").exists():
            continue
        case_dirs.append(path)
    return case_dirs


def compute_verdict_only_result(artifacts_dir: pathlib.Path, verdicts_fixture):
    verdicts_artifact_path = artifacts_dir / "verdict_only_verdicts.json"
    if not verdicts_artifact_path.exists():
        return None
    verdict_only_predicted = load_predicted_verdicts(verdicts_artifact_path)
    retrieved_context_path = (
        artifacts_dir / "verdict_only_retrieved_context.json"
    )
    retrieved_context: list[RetrievedContextRecord] = []
    if retrieved_context_path.exists():
        retrieved_context = load_retrieved_context(retrieved_context_path)
    return score_verdicts(
        verdict_only_predicted, verdicts_fixture, retrieved_context
    )


def metrics_for_case(
    case_dir: pathlib.Path,
    variant: str,
    run_label: str,
) -> dict[str, float | int | None] | None:
    artifacts_dir = run_dir(case_dir, variant, run_label)
    predicted_requirements_path = artifacts_dir / "predicted_requirements.json"
    if not predicted_requirements_path.exists():
        return None
    requirements_fixture = load_true_requirements(
        case_dir / "true_requirements.json"
    )
    verdicts_fixture = load_true_verdicts(
        true_verdicts_path(case_dir, variant)
    )
    predicted_requirements = load_predicted_requirements(
        predicted_requirements_path
    )
    predicted_verdicts = load_predicted_verdicts(
        artifacts_dir / "predicted_verdicts.json"
    )
    retrieved_context = load_retrieved_context(
        artifacts_dir / "predicted_retrieved_context.json"
    )
    report = evaluate(
        requirements_fixture, verdicts_fixture, predicted_requirements,
        predicted_verdicts, retrieved_context,
    )
    verdict_only_result = compute_verdict_only_result(
        artifacts_dir, verdicts_fixture
    )
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
