"""Build the DPO preference dataset for the verdict-generation step.

Reads sft/data/verdicts_train.jsonl (train split only -- validation/test
must stay untouched by preference-pair construction, same as they stay
untouched by SFT). For each row, samples N completions from the
currently-deployed SFT model at temperature > 0 through the same
OpenAI-compatible endpoint scripts/evaluate_verdicts.py and
sft/run_verdict_eval.py already use (so "on-policy" means genuinely
on-policy relative to how the model is actually served, not a separate
transformers.generate() call with different sampling internals). Any
sampled completion whose verdict label disagrees with the row's gold
label becomes a hard negative ("rejected"); the row's own gold
completion (already known correct, from Gemini/audited fixtures) is the
"chosen". Rows where every sample happens to agree with the gold label
are skipped -- there is no negative to pair against.

Deliberately does NOT synthesize or template a "wrong" rationale: the
rejected completion is always a full, real model generation (its own
verdict AND its own reasoning/evidence_quotes), so the pair never
contains an artificial mismatch between a wrong label and reasoning
text that argues for a different label. That would let DPO learn to
spot the internal contradiction instead of learning from the actual
requirement+evidence content.

Usage:
  python sft/build_dpo_dataset.py --samples-per-prompt 4 \
      --base-url http://localhost:8000/v1 --model Qwen/Qwen3-8B-AWQ
"""
import argparse
import json
import os
import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

DATA_DIR = "sft/data"


def load_jsonl(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _as_completion_dict(sample) -> dict:
    """Normalize a sampled VerdictResult (pydantic model) or a plain dict
    (as used directly in tests) to the same completion shape stored in
    verdicts_train.jsonl: {verdict, evidence_quotes, reasoning}."""
    if isinstance(sample, dict):
        return sample
    verdict = sample.verdict
    verdict_value = verdict.value if hasattr(verdict, "value") else verdict
    return {
        "verdict": verdict_value,
        "evidence_quotes": [
            q.model_dump() if hasattr(q, "model_dump") else q
            for q in sample.evidence_quotes
        ],
        "reasoning": sample.reasoning,
    }


def build_preference_row(row: dict, sampled_results: list) -> dict | None:
    """Pure pairing logic, no model calls -- this is what gets unit
    tested. `row` is one line from verdicts_train.jsonl. `sampled_results`
    is whatever build_negative_samples() returned for that row's prompt
    (a list of VerdictResult objects or, in tests, plain dicts with the
    same keys). Returns a dpo_train.jsonl row, or None if none of the
    samples disagreed with the gold verdict."""
    true_verdict = row["completion"]["verdict"]
    for sample in sampled_results:
        completion = _as_completion_dict(sample)
        if completion["verdict"] != true_verdict:
            return {
                "case": row["case"],
                "variant": row["variant"],
                "topic_id": row["topic_id"],
                "prompt": row["prompt"],
                "chosen": row["completion"],
                "rejected": completion,
            }
    return None


def build_negative_samples(prompt_text: str, samples_per_prompt: int):
    """Calls the currently-configured language model (env-var overridden
    by main() to point at the vLLM endpoint serving the SFT checkpoint)
    samples_per_prompt times at temperature > 0. Import is local so this
    module stays importable (and its pure logic testable) without the
    rest of the pipeline's dependencies for callers that only need
    build_preference_row."""
    from backends.llm_client import get_structured_chat_model, invoke_structured
    from steps.verdicts import VerdictResult

    structured_model = get_structured_chat_model(VerdictResult)
    results = []
    for _ in range(samples_per_prompt):
        try:
            results.append(invoke_structured(structured_model, prompt_text))
        except Exception as e:  # noqa: BLE001 -- one bad sample must not abort the batch
            print(f"    sample failed: {e}")
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples-per-prompt", type=int, default=4)
    parser.add_argument("--base-url", default="http://localhost:8000/v1")
    parser.add_argument("--model", default="Qwen/Qwen3-8B-AWQ")
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--output", default=f"{DATA_DIR}/dpo_train.jsonl")
    args = parser.parse_args()

    os.environ["LANGUAGE_MODEL_PROVIDER"] = "openai_compatible"
    os.environ["LANGUAGE_MODEL_BASE_URL"] = args.base_url
    os.environ["LANGUAGE_MODEL_NAME"] = args.model
    os.environ["LANGUAGE_MODEL_API_KEY"] = "not-needed"
    os.environ["LANGUAGE_MODEL_TEMPERATURE"] = str(args.temperature)

    train_rows = load_jsonl(f"{DATA_DIR}/verdicts_train.jsonl")
    print(f"{len(train_rows)} train rows loaded")

    pairs = []
    skipped_no_negative = 0
    for i, row in enumerate(train_rows):
        samples = build_negative_samples(row["prompt"], args.samples_per_prompt)
        pair = build_preference_row(row, samples)
        if pair is None:
            skipped_no_negative += 1
        else:
            pairs.append(pair)
        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{len(train_rows)} rows processed, "
                  f"{len(pairs)} pairs so far")

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        for pair in pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    print(f"\n{len(pairs)} preference pairs -> {args.output}")
    print(
        f"{skipped_no_negative} rows skipped "
        "(model agreed with gold on every sample)"
    )


if __name__ == "__main__":
    main()
