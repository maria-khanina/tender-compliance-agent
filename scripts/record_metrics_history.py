import argparse
import datetime
import json
import pathlib
import subprocess
import sys


def _add_project_root_to_path() -> None:
    project_root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Append one row per case to a JSONL history log of summary "
            "metrics, so a later run can be compared against earlier ones "
            "to see whether a change improved or regressed quality. Does "
            "not touch metrics_summary.md or aggregate_metrics.py."
        )
    )
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--output-prefix", default="predicted")
    parser.add_argument(
        "--history-file", default="data/metrics_history.jsonl"
    )
    parser.add_argument(
        "--label",
        help=(
            "Free-text note for this run (e.g. what changed since the "
            "last recorded run). Optional."
        ),
    )
    return parser.parse_args()


def _git_commit_sha() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return result.stdout.strip()


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
        predicted_requirements_path = (
            case_dir / f"{output_prefix}_requirements.json"
        )
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
            case_dir / f"{output_prefix}_verdicts.json"
        )
        retrieved_evidence = load_retrieved_evidence(
            case_dir / f"{output_prefix}_retrieved_evidence.json"
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

    arguments = _parse_arguments()
    data_dir = pathlib.Path(arguments.data_dir)
    recorded_at = datetime.datetime.now(datetime.UTC).isoformat()
    commit_sha = _git_commit_sha()
    history_path = pathlib.Path(arguments.history_file)

    rows_written = 0
    with history_path.open("a", encoding="utf-8") as history_file:
        for case_dir in find_case_dirs(data_dir):
            metrics = metrics_for_case(case_dir, arguments.output_prefix)
            if metrics is None:
                continue
            row = {
                "recorded_at": recorded_at,
                "commit": commit_sha,
                "label": arguments.label,
                "case": case_dir.name,
                **metrics,
            }
            history_file.write(json.dumps(row, ensure_ascii=False) + "\n")
            rows_written += 1

    print(f"Appended {rows_written} row(s) to {history_path}")


if __name__ == "__main__":
    main()
