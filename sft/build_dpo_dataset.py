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

One pair is kept per *distinct* wrong verdict label seen among the
samples for a row (not one per raw sample, and not just the first
mismatch) -- there are only 3 possible wrong labels, so this bounds
pairs-per-row at 3 regardless of --samples-per-prompt, while still
extracting every distinct failure mode a row exposes instead of only
the first one encountered. This also means raising --samples-per-prompt
is the direct lever against the pool of hard negatives shrinking as the
SFT model gets more accurate: more samples per prompt raise the odds of
surfacing at least one (and, up to 3, each) wrong label even at a low
per-sample error rate.

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
import concurrent.futures
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


def build_preference_rows(row: dict, sampled_results: list) -> list[dict]:
    """Pure pairing logic, no model calls -- this is what gets unit
    tested. `row` is one line from verdicts_train.jsonl. `sampled_results`
    is whatever build_negative_samples() returned for that row's prompt
    (a list of VerdictResult objects or, in tests, plain dicts with the
    same keys). Returns one dpo_train.jsonl row per distinct wrong
    verdict label found among the samples (see module docstring), or an
    empty list if every sample agreed with the gold verdict."""
    true_verdict = row["completion"]["verdict"]
    pairs = []
    seen_wrong_verdicts = set()
    for sample in sampled_results:
        completion = _as_completion_dict(sample)
        wrong_verdict = completion["verdict"]
        if wrong_verdict == true_verdict or wrong_verdict in seen_wrong_verdicts:
            continue
        seen_wrong_verdicts.add(wrong_verdict)
        pairs.append({
            "case": row["case"],
            "variant": row["variant"],
            "topic_id": row["topic_id"],
            "prompt": row["prompt"],
            "chosen": row["completion"],
            "rejected": completion,
        })
    return pairs


def merge_row_pairs(
    existing_pairs: list[dict], row: dict, sampled_results: list
) -> list[dict]:
    """Pure merge logic, no model calls -- also unit tested. Combines a
    row's already-known pairs (from a prior run's --output, possibly
    empty) with whatever build_preference_rows() finds among this run's
    fresh samples, deduplicated by rejected-verdict label so the same
    wrong label already on file is never appended twice and the 3-label
    cap (see module docstring) is respected across runs, not just within
    one. Existing pairs are always kept first and never dropped -- a
    top-up run can only add pairs for a row, never lose ones already
    found by an earlier run."""
    row_pairs = list(existing_pairs)
    seen_wrong_verdicts = {p["rejected"]["verdict"] for p in row_pairs}
    for new_pair in build_preference_rows(row, sampled_results):
        wrong_verdict = new_pair["rejected"]["verdict"]
        if wrong_verdict in seen_wrong_verdicts:
            continue
        seen_wrong_verdicts.add(wrong_verdict)
        row_pairs.append(new_pair)
    return row_pairs


def _sample_one(structured_model, prompt_text: str):
    """One on-policy sample, or None on failure -- isolated so a single
    bad generation can't abort the whole (row x sample) task pool when
    run concurrently.

    Deliberately calls .invoke() directly instead of the shared
    invoke_structured() -- that helper carries an 8-attempt retry
    (backends/retry.py, shared with the rest of the pipeline, where
    retrying transient errors is the right call). Here a failure is
    usually the model hitting the endpoint's max_model_len before
    closing its JSON (openai.LengthFinishReasonError) -- a deterministic
    property of that specific (prompt, sampled token path) pair, not a
    transient fault, so retrying it just burns up to 8x the generation
    time for the same doomed outcome. One attempt per sample is enough:
    --samples-per-prompt already sends several independent draws per
    row, so a single lost draw is absorbed the same way any other
    disagreeing sample would be."""
    try:
        return structured_model.invoke(prompt_text)
    except Exception as e:  # noqa: BLE001 -- one bad sample must not abort the batch
        print(f"    sample failed: {e}")
        return None


def build_negative_samples(prompt_text: str, samples_per_prompt: int):
    """Calls the currently-configured language model (env-var overridden
    by main() to point at the vLLM endpoint serving the SFT checkpoint)
    samples_per_prompt times at temperature > 0. Import is local so this
    module stays importable (and its pure logic testable) without the
    rest of the pipeline's dependencies for callers that only need
    build_preference_row. Kept sequential -- main() no longer calls this
    directly (it parallelizes across rows AND samples together via
    _sample_one), but the function stays for standalone/single-row use."""
    from backends.llm_client import get_structured_chat_model
    from steps.verdicts import VerdictResult

    structured_model = get_structured_chat_model(VerdictResult)
    results = []
    for _ in range(samples_per_prompt):
        sample = _sample_one(structured_model, prompt_text)
        if sample is not None:
            results.append(sample)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples-per-prompt", type=int, default=8)
    parser.add_argument("--base-url", default="http://localhost:8000/v1")
    parser.add_argument("--model", default="Qwen/Qwen3-8B-AWQ")
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--output", default=f"{DATA_DIR}/dpo_train.jsonl")
    parser.add_argument(
        "--max-workers", type=int, default=16,
        help="Concurrent in-flight requests against the inference endpoint. "
             "vLLM continuous-batches these, so this should be well above 1.",
    )
    parser.add_argument(
        "--only-known-hard-rows", action="store_true",
        help="Restrict sampling to rows that already have >=1 pair in "
             "--output, instead of all rows below the 3-pair cap. Use "
             "this when --model/--base-url point at a weaker or earlier "
             "checkpoint than the one that produced the existing pairs: "
             "that weaker model's mistakes on rows the target checkpoint "
             "already gets right every time are off-policy noise, not "
             "relevant hard negatives, so there is no reason to spend "
             "sampling budget re-discovering rows the target model isn't "
             "actually confused by. Only useful together with an "
             "existing --output to top up (otherwise nothing is sampled).",
    )
    args = parser.parse_args()

    os.environ["LANGUAGE_MODEL_PROVIDER"] = "openai_compatible"
    os.environ["LANGUAGE_MODEL_BASE_URL"] = args.base_url
    os.environ["LANGUAGE_MODEL_NAME"] = args.model
    os.environ["LANGUAGE_MODEL_API_KEY"] = "not-needed"
    os.environ["LANGUAGE_MODEL_TEMPERATURE"] = str(args.temperature)

    from backends.llm_client import get_structured_chat_model
    from steps.verdicts import VerdictResult

    structured_model = get_structured_chat_model(VerdictResult)

    train_rows = load_jsonl(f"{DATA_DIR}/verdicts_train.jsonl")
    print(f"{len(train_rows)} train rows loaded")

    # Top-up semantics: a prior run's output at --output (if present) is
    # merged with, not overwritten -- pairs already found for a row are
    # kept, and only rows still short of the 3-distinct-wrong-verdicts
    # cap get resampled. This makes raising --samples-per-prompt after an
    # earlier low-yield run additive instead of a from-scratch redo.
    existing_pairs_by_row: dict[tuple, list[dict]] = {}
    if os.path.exists(args.output):
        for pair in load_jsonl(args.output):
            key = (pair["case"], pair["variant"], pair["topic_id"])
            existing_pairs_by_row.setdefault(key, []).append(pair)
        print(
            f"{len(existing_pairs_by_row)} rows with existing pairs loaded "
            f"from {args.output} -- topping up"
        )

    def row_key(row: dict) -> tuple:
        return (row["case"], row["variant"], row["topic_id"])

    rows_to_sample = [
        (i, row)
        for i, row in enumerate(train_rows)
        if len(existing_pairs_by_row.get(row_key(row), [])) < 3
        and (
            not args.only_known_hard_rows
            or row_key(row) in existing_pairs_by_row
        )
    ]
    if args.only_known_hard_rows:
        print(
            f"--only-known-hard-rows set: restricting to "
            f"{len(existing_pairs_by_row)} rows with existing pairs "
            f"(of which {len(rows_to_sample)} are below the 3-pair cap)"
        )
    print(
        f"{len(train_rows) - len(rows_to_sample)} rows already at the "
        f"3-pair cap, skipped; sampling {len(rows_to_sample)} rows"
    )

    # Written incrementally (one row's worth at a time, flushed
    # immediately) rather than built up in memory and written once at the
    # end -- a run this slow (hours, per the first pass) needs to be safe
    # to kill and resume: on-disk output after any interruption is always
    # exactly "every row that has fully finished so far", which is a
    # valid, directly re-mergeable --output for the next invocation.
    os.makedirs(DATA_DIR, exist_ok=True)
    pairs_written = 0
    skipped_no_negative = 0
    not_sampled_this_run = 0

    def _write_row_pairs(f, row_pairs: list[dict]) -> None:
        nonlocal pairs_written, skipped_no_negative
        if not row_pairs:
            skipped_no_negative += 1
            return
        for pair in row_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")
        pairs_written += len(row_pairs)
        f.flush()

    rows_to_sample_indices = {i for i, _ in rows_to_sample}
    with open(args.output, "w", encoding="utf-8") as out_f:
        # Rows not being (re)sampled this run -- either already at the cap,
        # or (with --only-known-hard-rows) never had a pair to begin with
        # -- are carried over unchanged; .get(..., []) covers both, since
        # only rows with >=1 existing pair have an entry in the dict. A
        # never-sampled, zero-pair row is counted separately below so it
        # isn't conflated with a row this run actually sampled and found
        # nothing new for.
        for i, row in enumerate(train_rows):
            if i not in rows_to_sample_indices:
                row_pairs = existing_pairs_by_row.get(row_key(row), [])
                if not row_pairs:
                    not_sampled_this_run += 1
                else:
                    _write_row_pairs(out_f, row_pairs)

        # Flatten the full (row x sample) task grid so every in-flight
        # request competes for vLLM's continuous batching, instead of only
        # ever having one request in flight (samples_per_prompt sequential
        # calls per row, rows processed one at a time) -- while still
        # tracking per-row completion so each row can be written the
        # moment its own samples are all in, independent of the others.
        remaining_per_row = {i: args.samples_per_prompt for i, _ in rows_to_sample}
        samples_by_row: dict[int, list] = {i: [] for i, _ in rows_to_sample}
        rows_by_index = dict(rows_to_sample)
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=args.max_workers
        ) as pool:
            future_to_row = {
                pool.submit(_sample_one, structured_model, row["prompt"]): i
                for i, row in rows_to_sample
                for _ in range(args.samples_per_prompt)
            }
            done = 0
            total = len(future_to_row)
            for future in concurrent.futures.as_completed(future_to_row):
                row_index = future_to_row[future]
                sample = future.result()
                if sample is not None:
                    samples_by_row[row_index].append(sample)
                remaining_per_row[row_index] -= 1
                done += 1
                if done % 50 == 0:
                    print(f"  {done}/{total} samples generated")

                if remaining_per_row[row_index] == 0:
                    row = rows_by_index[row_index]
                    key = row_key(row)
                    row_pairs = merge_row_pairs(
                        existing_pairs_by_row.get(key, []),
                        row,
                        samples_by_row[row_index],
                    )
                    _write_row_pairs(out_f, row_pairs)
                    # Free the per-row sample buffer once written -- no
                    # further use for it, and some rows carry several
                    # thousand-token completions.
                    del samples_by_row[row_index]

    print(f"\n{pairs_written} preference pairs -> {args.output}")
    print(
        f"{skipped_no_negative} rows sampled this run but found nothing new "
        "(model agreed with gold, or only reproduced already-known labels)"
    )
    if not_sampled_this_run:
        print(
            f"{not_sampled_this_run} rows not sampled this run "
            "(--only-known-hard-rows, no prior pair to top up)"
        )


if __name__ == "__main__":
    main()
