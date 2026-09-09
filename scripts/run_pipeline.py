import argparse
import json
import pathlib
import sys
from collections.abc import Sequence

from pydantic import BaseModel


def _add_project_root_to_path() -> None:
    project_root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the tender compliance pipeline."
    )
    parser.add_argument("--requirements", required=True)
    parser.add_argument("--application", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def _write_json_list(
    path: pathlib.Path,
    items: Sequence[BaseModel],
) -> None:
    serializable_items = [item.model_dump(mode="json") for item in items]
    path.write_text(
        json.dumps(serializable_items, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> None:
    _add_project_root_to_path()
    from logging_config import configure_logging, get_logger
    from pipeline import run_pipeline
    from schemas import PipelineResult

    configure_logging()
    logger = get_logger(__name__)

    def run_or_exit(
        requirements_path: str,
        application_path: str,
    ) -> PipelineResult:
        try:
            return run_pipeline(requirements_path, application_path)
        except Exception as pipeline_error:
            logger.error("Pipeline run failed: %s", pipeline_error)
            sys.exit(1)

    def output_paths(
        output_path: pathlib.Path,
    ) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
        requirements_path = output_path.with_name(
            output_path.stem + "_requirements.json"
        )
        verdicts_path = output_path.with_name(
            output_path.stem + "_verdicts.json"
        )
        retrieved_evidence_path = output_path.with_name(
            output_path.stem + "_retrieved_evidence.json"
        )
        return requirements_path, verdicts_path, retrieved_evidence_path

    def write_outputs(
        output_path: pathlib.Path,
        result: PipelineResult,
        paths: tuple[pathlib.Path, pathlib.Path, pathlib.Path],
    ) -> None:
        requirements_path, verdicts_path, retrieved_evidence_path = paths
        output_path.write_text(result.report, encoding="utf-8")
        _write_json_list(requirements_path, result.requirements)
        _write_json_list(verdicts_path, result.verdicts)
        _write_json_list(retrieved_evidence_path, result.retrieved_evidence)
        print(f"Report written to {output_path}")
        print(f"Requirements written to {requirements_path}")
        print(f"Verdicts written to {verdicts_path}")
        print(f"Retrieved evidence written to {retrieved_evidence_path}")

    arguments = _parse_arguments()
    result = run_or_exit(arguments.requirements, arguments.application)
    output_path = pathlib.Path(arguments.output)
    write_outputs(output_path, result, output_paths(output_path))


if __name__ == "__main__":
    main()
