import argparse
import json
import pathlib
import sys


def _add_project_root_to_path() -> None:
    project_root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the verdict-generation step in isolation: run it "
            "directly on true_requirements.json's own text and citations "
            "against application.txt, bypassing requirement extraction "
            "and match-group sequencing entirely."
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


def _generate_predictions(synthetic_requirements, collection_name):
    from schemas import RetrievedContextRecord, Verdict
    from steps.evidence_retrieval import retrieve_context_chunks
    from steps.verdicts import generate_verdict

    predicted_verdicts: list[Verdict] = []
    retrieved_context: list[RetrievedContextRecord] = []
    for requirement in synthetic_requirements:
        if not requirement.is_text_verifiable:
            continue
        context_chunks = retrieve_context_chunks(
            requirement.text, collection_name
        )
        retrieved_context.append(RetrievedContextRecord(
            requirement_id=requirement.requirement_id,
            retrieved_context=context_chunks,
        ))
        predicted_verdicts.append(
            generate_verdict(requirement, context_chunks)
        )
    return predicted_verdicts, retrieved_context


def _write_json_artifact(path: pathlib.Path, records: list, label: str) -> None:
    serialized = [record.model_dump(mode="json") for record in records]
    path.write_text(
        json.dumps(serialized, indent=2, ensure_ascii=False), encoding="utf-8",
    )
    print(f"{label} written to {path}")


def _write_report(arguments: argparse.Namespace, report_text: str) -> None:
    if arguments.report_output:
        report_output_path = pathlib.Path(arguments.report_output)
        report_output_path.write_text(report_text, encoding="utf-8")
        print(f"Verdict-only evaluation report written to {report_output_path}")
    else:
        print(report_text)


def main() -> None:
    _add_project_root_to_path()
    from backends.vectorstore import case_collection_name, index_chunks
    from evaluation.fixtures import load_true_requirements, load_true_verdicts
    from evaluation.verdict_only import (
        build_synthetic_requirements,
        render_verdict_only_report,
        score_verdicts,
    )
    from steps.chunking import split_application_document
    from case_layout import application_path as case_application_path
    from case_layout import run_dir, true_verdicts_path

    arguments = _parse_arguments()
    case_dir = pathlib.Path(arguments.case_dir)
    variant = arguments.variant

    requirements_fixture = load_true_requirements(
        case_dir / "true_requirements.json"
    )
    verdicts_fixture = load_true_verdicts(
        true_verdicts_path(case_dir, variant)
    )

    collection_name = case_collection_name(f"{case_dir.name}_{variant}")

    application_path = case_application_path(case_dir, variant)
    application_text = application_path.read_text(encoding="utf-8")
    application_chunks = split_application_document(
        application_text, application_path.as_posix()
    )
    index_chunks(collection_name, application_chunks)

    synthetic_requirements = build_synthetic_requirements(requirements_fixture)
    predicted_verdicts, retrieved_context = _generate_predictions(
        synthetic_requirements, collection_name
    )

    artifacts_dir = run_dir(case_dir, variant, arguments.run_label)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    _write_json_artifact(
        artifacts_dir / "verdict_only_verdicts.json",
        predicted_verdicts,
        "Verdict-only raw verdicts",
    )
    _write_json_artifact(
        artifacts_dir / "verdict_only_retrieved_context.json",
        retrieved_context,
        "Verdict-only retrieved context",
    )

    result = score_verdicts(
        predicted_verdicts, verdicts_fixture, retrieved_context
    )
    _write_report(arguments, render_verdict_only_report(result))


if __name__ == "__main__":
    main()
