import argparse
import json
import pathlib
from typing import TypedDict

from case_layout import application_path as case_application_path
from case_layout import run_dir, true_verdicts_path
from config import (
    CLI_QUOTE_PREVIEW_CHARACTER_COUNT,
    DEFAULT_APPLICATION_VARIANT,
    DEFAULT_RUN_LABEL,
    RETRIEVAL_ONLY_EVAL_COLLECTION_PREFIX,
)
from evaluation.fixtures import load_true_requirements, load_true_verdicts
from evaluation.verdict_only import build_synthetic_requirements
from schemas import Requirement


class RetrievalRow(TypedDict):
    topic_id: str
    gold_evidence_count: int
    found_count: int
    missed_quotes: list[str]
    retrieved_chunk_count: int


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
        default=DEFAULT_APPLICATION_VARIANT,
        help=(
            "Application variant directory name under applications/ "
            "(e.g. 'a', 'b', 'c'). Defaults to 'a', the case's canonical "
            "application."
        ),
    )
    parser.add_argument("--run-label", default=DEFAULT_RUN_LABEL)
    parser.add_argument("--report-output")
    return parser.parse_args()


def _score_requirement_retrieval(
    requirement: Requirement,
    gold_quotes: list[str],
    collection_name: str,
) -> RetrievalRow:
    from steps.evidence_retrieval import retrieve_context_chunks

    context_chunks = retrieve_context_chunks(requirement.text, collection_name)
    retrieved_texts = [chunk.text for chunk in context_chunks]
    found: list[str] = []
    missed: list[str] = []
    for quote in gold_quotes:
        stripped_quote = quote.strip()
        hit = any(
            stripped_quote and stripped_quote in text for text in retrieved_texts
        )
        (found if hit else missed).append(quote)
    return {
        "topic_id": requirement.requirement_id,
        "gold_evidence_count": len(gold_quotes),
        "found_count": len(found),
        "missed_quotes": missed,
        "retrieved_chunk_count": len(retrieved_texts),
    }


def _score_retrieval(
    synthetic_requirements: list[Requirement],
    gold_evidence_by_topic: dict[str, list[str]],
    collection_name: str,
) -> tuple[list[RetrievalRow], int, int]:
    rows: list[RetrievalRow] = []
    for requirement in synthetic_requirements:
        if not requirement.is_text_verifiable:
            continue
        gold_quotes = gold_evidence_by_topic.get(requirement.requirement_id, [])
        if not gold_quotes:
            continue
        rows.append(_score_requirement_retrieval(
            requirement, gold_quotes, collection_name
        ))
    total_gold = sum(row["gold_evidence_count"] for row in rows)
    total_found = sum(row["found_count"] for row in rows)
    return rows, total_gold, total_found


def _render_retrieval_report(
    rows: list[RetrievalRow],
    total_gold: int,
    total_found: int,
) -> str:
    recall = total_found / total_gold if total_gold else None
    incomplete = [row for row in rows if row["missed_quotes"]]

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
    for row in incomplete:
        report_lines.append(
            f"- `{row['topic_id']}`: "
            f"{row['found_count']}/{row['gold_evidence_count']} "
            f"found, {row['retrieved_chunk_count']} chunks retrieved"
        )
        for quote in row["missed_quotes"]:
            preview = quote[:CLI_QUOTE_PREVIEW_CHARACTER_COUNT]
            report_lines.append(f"  - **missed:** \"{preview}\"")
    return "\n".join(report_lines)


def _write_outputs(
    arguments: argparse.Namespace,
    case_dir: pathlib.Path,
    variant: str,
    report_text: str,
    rows: list[RetrievalRow],
    total_gold: int,
    total_found: int,
) -> None:
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
        "recall": total_found / total_gold if total_gold else None,
        "total_gold": total_gold,
        "total_found": total_found,
        "rows": rows,
    }
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> None:
    arguments = _parse_arguments()
    from backends.vectorstore import case_collection_name, index_chunks
    from steps.chunking import split_application_document

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
        f"{RETRIEVAL_ONLY_EVAL_COLLECTION_PREFIX}{case_dir.name}_{variant}"
    )
    index_chunks(collection_name, application_chunks)

    synthetic_requirements = build_synthetic_requirements(requirements_fixture)
    rows, total_gold, total_found = _score_retrieval(
        synthetic_requirements, gold_evidence_by_topic, collection_name
    )
    report_text = _render_retrieval_report(rows, total_gold, total_found)
    _write_outputs(
        arguments, case_dir, variant, report_text, rows, total_gold, total_found
    )


if __name__ == "__main__":
    main()
