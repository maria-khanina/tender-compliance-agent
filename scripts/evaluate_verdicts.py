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
        default="",
        help=(
            "Application variant suffix (e.g. 'b' for application_b.txt / "
            "true_verdicts_b.json). true_requirements.json is always shared "
            "and never suffixed. Omit for the case's default application.txt "
            "/ true_verdicts.json."
        ),
    )
    parser.add_argument("--report-output")
    return parser.parse_args()


def main() -> None:
    _add_project_root_to_path()
    from backends.vectorstore import case_collection_name, index_chunks
    from evaluation.fixtures import load_true_requirements, load_true_verdicts
    from evaluation.verdict_only import (
        build_synthetic_requirements,
        render_verdict_only_report,
        score_verdicts,
    )
    from schemas import RetrievedEvidenceRecord, Verdict
    from steps.chunking import split_application_document
    from steps.evidence_retrieval import retrieve_evidence_chunks
    from steps.verdicts import generate_verdict

    arguments = _parse_arguments()
    case_dir = pathlib.Path(arguments.case_dir)
    suffix = f"_{arguments.variant}" if arguments.variant else ""

    requirements_fixture = load_true_requirements(
        case_dir / "true_requirements.json"
    )
    verdicts_fixture = load_true_verdicts(
        case_dir / f"true_verdicts{suffix}.json"
    )

    collection_name = case_collection_name(f"{case_dir.name}{suffix}")

    application_path = case_dir / f"application{suffix}.txt"
    application_text = application_path.read_text(encoding="utf-8")
    application_chunks = split_application_document(
        application_text, str(application_path)
    )
    index_chunks(collection_name, application_chunks)

    synthetic_requirements = build_synthetic_requirements(
        requirements_fixture
    )
    predicted_verdicts: list[Verdict] = []
    retrieved_evidence: list[RetrievedEvidenceRecord] = []
    for requirement in synthetic_requirements:
        if not requirement.is_text_verifiable:
            continue
        evidence_chunks = retrieve_evidence_chunks(
            requirement.text, collection_name
        )
        retrieved_evidence.append(RetrievedEvidenceRecord(
            requirement_id=requirement.requirement_id,
            evidence_chunks=evidence_chunks,
        ))
        predicted_verdicts.append(
            generate_verdict(requirement, evidence_chunks)
        )

    verdicts_artifact_path = case_dir / f"verdict_only_verdicts{suffix}.json"
    serializable_verdicts = [
        verdict.model_dump(mode="json") for verdict in predicted_verdicts
    ]
    verdicts_artifact_path.write_text(
        json.dumps(serializable_verdicts, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Verdict-only raw verdicts written to {verdicts_artifact_path}")

    retrieved_evidence_artifact_path = (
        case_dir / f"verdict_only_retrieved_evidence{suffix}.json"
    )
    serializable_retrieved_evidence = [
        record.model_dump(mode="json") for record in retrieved_evidence
    ]
    retrieved_evidence_artifact_path.write_text(
        json.dumps(
            serializable_retrieved_evidence, indent=2, ensure_ascii=False
        ),
        encoding="utf-8",
    )
    print(
        f"Verdict-only retrieved evidence written to "
        f"{retrieved_evidence_artifact_path}"
    )

    result = score_verdicts(
        predicted_verdicts, verdicts_fixture, retrieved_evidence
    )
    report_text = render_verdict_only_report(result)
    if arguments.report_output:
        report_output_path = pathlib.Path(arguments.report_output)
        report_output_path.write_text(report_text, encoding="utf-8")
        print(f"Verdict-only evaluation report written to {report_output_path}")
    else:
        print(report_text)


if __name__ == "__main__":
    main()
