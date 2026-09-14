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
            "Evaluate the retrieval step in isolation: for every "
            "is_text_verifiable topic in true_requirements.json, run "
            "retrieve_context_chunks against the indexed application and "
            "check whether true_verdicts.json's own evidence quotes for "
            "that topic actually land in the retrieved context -- bypasses "
            "extraction and verdict generation entirely."
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
    from backends.vectorstore import case_collection_name, index_chunks
    from evaluation.fixtures import load_true_requirements, load_true_verdicts
    from evaluation.verdict_only import build_synthetic_requirements
    from steps.chunking import split_application_document
    from steps.evidence_retrieval import retrieve_context_chunks
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
    gold_evidence_by_topic = {
        v.topic_id: [e.quote for e in v.evidence] for v in verdicts_fixture.verdicts
    }

    application_path = case_application_path(case_dir, variant)
    application_text = application_path.read_text(encoding="utf-8")
    application_chunks = split_application_document(
        application_text, application_path.as_posix()
    )
    collection_name = case_collection_name(
        f"retrieval_only_{case_dir.name}_{variant}"
    )
    index_chunks(collection_name, application_chunks)

    synthetic_requirements = build_synthetic_requirements(requirements_fixture)

    rows = []
    total_gold = 0
    total_found = 0
    for requirement in synthetic_requirements:
        if not requirement.is_text_verifiable:
            continue
        gold_quotes = gold_evidence_by_topic.get(requirement.requirement_id, [])
        if not gold_quotes:
            continue
        context_chunks = retrieve_context_chunks(
            requirement.text, collection_name
        )
        retrieved_texts = [c.text for c in context_chunks]
        found = []
        missed = []
        for quote in gold_quotes:
            stripped_quote = quote.strip()
            hit = any(
                stripped_quote and stripped_quote in text
                for text in retrieved_texts
            )
            (found if hit else missed).append(quote)
        total_gold += len(gold_quotes)
        total_found += len(found)
        rows.append({
            "topic_id": requirement.requirement_id,
            "gold_evidence_count": len(gold_quotes),
            "found_count": len(found),
            "missed_quotes": missed,
            "retrieved_chunk_count": len(retrieved_texts),
        })

    recall = total_found / total_gold if total_gold else None
    incomplete = [r for r in rows if r["missed_quotes"]]

    report_lines = ["## Retrieval-only evaluation", ""]
    report_lines.append(
        "Runs the real retrieval step directly against true_requirements.json "
        "+ application.txt, bypassing extraction and verdict generation -- "
        "checks whether true_verdicts.json's own gold evidence quotes are "
        "among the chunks the verdict step would actually be shown."
    )
    report_lines.append("")
    if recall is not None:
        report_lines.append(
            f"**Evidence recall: {recall * 100:.1f}% "
            f"({total_found}/{total_gold} gold evidence spans found in "
            f"retrieved context, across {len(rows)} topics with gold evidence)**"
        )
    else:
        report_lines.append("No topics with gold evidence to score.")
    report_lines.append("")
    if not incomplete:
        report_lines.append("- none (every gold evidence span was retrieved)")
    for r in incomplete:
        report_lines.append(
            f"- `{r['topic_id']}`: {r['found_count']}/{r['gold_evidence_count']} "
            f"found, {r['retrieved_chunk_count']} chunks retrieved"
        )
        for m in r["missed_quotes"]:
            report_lines.append(f"  - **missed:** \"{m[:200]}\"")
    report_text = "\n".join(report_lines)

    if arguments.report_output:
        pathlib.Path(arguments.report_output).write_text(
            report_text, encoding="utf-8"
        )
        print(f"Retrieval-only evaluation report written to {arguments.report_output}")
    else:
        print(report_text)

    artifacts_dir = run_dir(case_dir, variant, arguments.run_label)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    summary_path = artifacts_dir / "retrieval_only_summary.json"
    summary = {
        "recall": recall,
        "total_gold": total_gold,
        "total_found": total_found,
        "rows": rows,
    }
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
