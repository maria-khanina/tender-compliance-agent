import argparse
import datetime
import json
import pathlib
import subprocess

from config import (
    DEFAULT_APPLICATION_VARIANT,
    DEFAULT_RUN_LABEL,
    REQUIREMENT_DEDUPLICATION_CANDIDATE_SIMILARITY_THRESHOLD,
    Settings,
)
from evaluation.case_metrics import find_case_dirs, metrics_for_case


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
    parser.add_argument("--variant", default=DEFAULT_APPLICATION_VARIANT)
    parser.add_argument("--run-label", default=DEFAULT_RUN_LABEL)
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


def _git_dirty_paths(paths: list[str]) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--", *paths],
            capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    dirty = []
    for line in result.stdout.splitlines():
        if line.strip():
            dirty.append(line[3:].strip())
    return dirty


def main() -> None:
    arguments = _parse_arguments()
    data_dir = pathlib.Path(arguments.data_dir)
    recorded_at = datetime.datetime.now(datetime.UTC).isoformat()
    commit_sha = _git_commit_sha()
    history_path = pathlib.Path(arguments.history_file)

    language_model_name = Settings().language_model_name  # type: ignore[call-arg]
    dedup_threshold = REQUIREMENT_DEDUPLICATION_CANDIDATE_SIMILARITY_THRESHOLD
    dirty_paths = _git_dirty_paths(["config.py", "prompts.py"])
    if dirty_paths:
        print(
            "WARNING: uncommitted changes in "
            f"{', '.join(dirty_paths)} -- the recorded commit will NOT "
            "match the code that actually produced these predicted_*.json "
            "files. Commit first if you want this checkpoint to be "
            "reproducible from the commit alone."
        )

    rows_written = 0
    with history_path.open("a", encoding="utf-8") as history_file:
        for case_dir in find_case_dirs(data_dir):
            metrics = metrics_for_case(
                case_dir, arguments.variant, arguments.run_label
            )
            if metrics is None:
                continue
            row = {
                "recorded_at": recorded_at,
                "commit": commit_sha,
                "commit_dirty_paths": dirty_paths,
                "label": arguments.label,
                "case": case_dir.name,
                "language_model_name": language_model_name,
                "dedup_threshold": dedup_threshold,
                **metrics,
            }
            history_file.write(json.dumps(row, ensure_ascii=False) + "\n")
            rows_written += 1

    print(f"Appended {rows_written} row(s) to {history_path}")


if __name__ == "__main__":
    main()
