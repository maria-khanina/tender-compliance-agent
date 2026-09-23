"""Build the verdict-generation SFT dataset (JSONL) from every case's
fixtures. Uses the real retrieval step for context (not the fixture's own
evidence quotes) so the prompt matches inference-time distribution; gold
evidence quotes are only used for the target's citations. Indexes under a
"sft_" Qdrant prefix to avoid colliding with concurrent sessions. Discovers
every application*/true_verdicts* variant pair per case, not just canonical.
"""
import glob
import json
import os
import pathlib
import sys
from typing import TYPE_CHECKING, cast

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from sft.training_config import SFT_DATASET_COLLECTION_PREFIX  # noqa: E402

if TYPE_CHECKING:
    from evaluation.fixtures import TrueEvidenceSpan
    from schemas import Chunk
    from sft.schemas import EvidenceQuote
    from sft.schemas import EvidenceRole as SftEvidenceRole

SPLIT_CONFIG = json.load(open("sft/split.json", encoding="utf-8"))
TEST_CASES = set(SPLIT_CONFIG["test"])
VAL_CASES = set(SPLIT_CONFIG["validation"])


def split_for_case(case_name: str) -> str:
    if case_name in TEST_CASES:
        return "test"
    if case_name in VAL_CASES:
        return "validation"
    return "train"


def discover_variants(case_dir: str) -> list[tuple[str, str, str]]:
    """Return (variant_label, application_path, true_verdicts_path)."""
    from case_layout import application_path as case_application_path
    from case_layout import discover_variants as discover_case_variants
    from case_layout import true_verdicts_path as case_true_verdicts_path

    case_path = pathlib.Path(case_dir)
    variants = []
    for variant in discover_case_variants(case_path):
        variants.append((
            variant,
            case_application_path(case_path, variant).as_posix(),
            str(case_true_verdicts_path(case_path, variant)),
        ))
    return variants


def infer_role(primary_verdict: str) -> "SftEvidenceRole":
    from schemas import EvidenceRole

    if primary_verdict == "compliant":
        return cast("SftEvidenceRole", EvidenceRole.SUPPORTS.value)
    if primary_verdict == "non_compliant":
        return cast("SftEvidenceRole", EvidenceRole.CONTRADICTS.value)
    return cast("SftEvidenceRole", EvidenceRole.INCONCLUSIVE.value)


def map_evidence_to_chunks(
    fixture_evidence: list["TrueEvidenceSpan"],
    retrieved_chunks: list["Chunk"],
    role: "SftEvidenceRole",
) -> tuple[list["EvidenceQuote"], int]:
    """Best-effort: locate each fixture evidence quote inside the actually
    retrieved chunks, so the target completion cites a real chunk_index the
    model could have produced. Silently drops quotes retrieval didn't
    surface -- known simplification, see module docstring."""
    quotes: list["EvidenceQuote"] = []
    unmatched = 0
    for ev in fixture_evidence:
        needle = ev.quote.strip()
        found = False
        for chunk in retrieved_chunks:
            if needle and needle in chunk.text:
                quotes.append({
                    "chunk_index": chunk.chunk_index,
                    "quote": needle,
                    "role": role,
                })
                found = True
                break
        if not found:
            unmatched += 1
    return quotes, unmatched


def build_examples_for_case(case_dir: str) -> list[dict[str, object]]:
    from backends.vectorstore import index_chunks
    from evaluation.fixtures import load_true_requirements, load_true_verdicts
    from prompts import VERDICT_GENERATION_PROMPT
    from steps.chunking import split_application_document
    from steps.evidence_retrieval import retrieve_context_chunks
    from steps.text_matching import format_chunks_as_prompt_text

    case_name = os.path.basename(case_dir)
    req_path = os.path.join(case_dir, "true_requirements.json")
    if not os.path.exists(req_path):
        return []
    requirements_fixture = load_true_requirements(pathlib.Path(req_path))
    description_by_topic = {
        r.topic_id: r.description for r in requirements_fixture.requirements
    }

    examples = []
    total_unmatched = 0
    for variant, app_path, verd_path in discover_variants(case_dir):
        verdicts_fixture = load_true_verdicts(pathlib.Path(verd_path))
        application_text = open(app_path, encoding="utf-8").read()
        application_chunks = split_application_document(
            application_text, app_path
        )
        collection_name = f"{SFT_DATASET_COLLECTION_PREFIX}{case_name}_{variant}"
        index_chunks(collection_name, application_chunks)

        for v in verdicts_fixture.verdicts:
            if not v.primary_verdict:
                continue
            requirement_text = description_by_topic.get(v.topic_id)
            if requirement_text is None:
                continue
            retrieved_chunks = retrieve_context_chunks(
                requirement_text, collection_name
            )
            context_text = format_chunks_as_prompt_text(retrieved_chunks)
            prompt_text = VERDICT_GENERATION_PROMPT.format(
                requirement_text=requirement_text,
                context_text=context_text,
            )
            role = infer_role(v.primary_verdict)
            evidence_quotes, unmatched = map_evidence_to_chunks(
                v.evidence, retrieved_chunks, role
            )
            total_unmatched += unmatched
            target = {
                "verdict": v.primary_verdict,
                "evidence_quotes": evidence_quotes,
                "reasoning": v.rationale,
            }
            examples.append({
                "case": case_name,
                "variant": variant,
                "topic_id": v.topic_id,
                "split": split_for_case(case_name),
                "primary_verdict_source": v.primary_verdict_source,
                "prompt": prompt_text,
                "completion": target,
            })
    if total_unmatched:
        print(f"  ({case_name}: {total_unmatched} fixture evidence quotes "
              f"not found in retrieved chunks -- dropped from targets)")
    return examples


def main():
    case_dirs = sorted(
        d for d in glob.glob("data/*")
        if os.path.isdir(d)
        and os.path.exists(os.path.join(d, "true_requirements.json"))
    )
    all_examples = []
    for case_dir in case_dirs:
        examples = build_examples_for_case(case_dir)
        print(f"{os.path.basename(case_dir):30s} {len(examples):3d} examples")
        all_examples.extend(examples)

    os.makedirs("sft/data", exist_ok=True)
    by_split = {"train": [], "validation": [], "test": []}
    for ex in all_examples:
        by_split[ex["split"]].append(ex)

    for split_name, rows in by_split.items():
        out_path = f"sft/data/verdicts_{split_name}.jsonl"
        with open(out_path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{split_name}: {len(rows)} examples -> {out_path}")


if __name__ == "__main__":
    main()
