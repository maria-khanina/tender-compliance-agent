"""Mine on-policy DPO preference pairs by sampling directly from the
merged SFT model via transformers, in the SAME bnb-4bit quantization
training used -- not through vLLM. This sidesteps the quantization
mismatch that made the Qwen3-8B run's vLLM/AWQ-served pairs unreliable:
there is no separately-downloaded AWQ artifact in this run, only the
bnb-4bit-quantized merged checkpoint, so what generates the samples here
is exactly what train_dpo.py will start DPO from.

Uses num_return_sequences to get --samples-per-prompt samples for one
row in a single batched generate() call (real, if modest, concurrency
within a row -- not across rows, since prompts differ in length and
padding a full cross-row batch isn't worth the complexity here).

Usage:
  python sft/mine_dpo_pairs_local.py --samples-per-prompt 8
"""
import argparse
import json
import os
import re
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

RUN_DIR = "sft/runs/qwen3-4b-v1"
MERGED_MODEL_DIR = f"{RUN_DIR}/merged"
DATA_DIR = "sft/data"
OUTPUT_PATH = f"{RUN_DIR}/dpo_train.jsonl"

VERDICT_LABELS = [
    "compliant", "non_compliant", "insufficient_information", "contradictory",
]


def load_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def extract_tool_call_json(generated_text: str) -> dict | None:
    """Parses the <tool_call>{...}</tool_call> block (or a bare JSON
    object, in case the model drops the tags) into {"name", "arguments"}
    or, if arguments parses as a dict with a "verdict" key, directly into
    the completion dict shape {verdict, evidence_quotes, reasoning}."""
    match = re.search(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", generated_text, re.DOTALL)
    raw = match.group(1) if match else generated_text.strip()
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if "arguments" in obj:
        args = obj["arguments"]
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                return None
        obj = args
    if not isinstance(obj, dict) or obj.get("verdict") not in VERDICT_LABELS:
        return None
    if "evidence_quotes" not in obj or "reasoning" not in obj:
        return None
    return obj


def build_preference_rows(row: dict, sampled_completions: list[dict]) -> list[dict]:
    true_verdict = row["completion"]["verdict"]
    pairs = []
    seen = set()
    for completion in sampled_completions:
        wrong_verdict = completion["verdict"]
        if wrong_verdict == true_verdict or wrong_verdict in seen:
            continue
        seen.add(wrong_verdict)
        pairs.append({
            "case": row["case"], "variant": row["variant"], "topic_id": row["topic_id"],
            "prompt": row["prompt"], "chosen": row["completion"], "rejected": completion,
        })
    return pairs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples-per-prompt", type=int, default=8)
    parser.add_argument("--max-new-tokens", type=int, default=300)
    parser.add_argument("--temperature", type=float, default=0.8)
    args = parser.parse_args()

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(MERGED_MODEL_DIR)
    tokenizer.padding_side = "left"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        MERGED_MODEL_DIR, quantization_config=bnb_config,
        device_map="auto", torch_dtype=torch.bfloat16,
    )
    model.eval()

    from sft.train_verdict_lora import TOOL_SCHEMA
    train_rows = load_jsonl(f"{DATA_DIR}/verdicts_train.jsonl")
    print(f"{len(train_rows)} train rows loaded", flush=True)

    # Resume support: a prior interrupted run's rows are already flushed to
    # OUTPUT_PATH one at a time (see out_f.flush() below), so on restart we
    # can just skip whatever row keys are already there and append instead
    # of overwriting -- this run OOM'd cold at row 250/431 after ~94min,
    # losing that work to a restart-from-scratch would be wasteful.
    already_done = set()
    if os.path.exists(OUTPUT_PATH):
        for line in open(OUTPUT_PATH, encoding="utf-8"):
            line = line.strip()
            if line:
                p = json.loads(line)
                already_done.add((p["case"], p["variant"], p["topic_id"]))
        print(f"{len(already_done)} rows already done, resuming", flush=True)

    pairs_written = 0
    skipped_no_negative = 0
    t0 = time.time()
    with open(OUTPUT_PATH, "a", encoding="utf-8") as out_f:
        for i, row in enumerate(train_rows):
            if (row["case"], row["variant"], row["topic_id"]) in already_done:
                continue
            input_text = tokenizer.apply_chat_template(
                [{"role": "user", "content": row["prompt"]}],
                tools=[TOOL_SCHEMA], add_generation_prompt=True,
                tokenize=False, enable_thinking=False,
            )
            inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
            with torch.no_grad():
                output_ids = model.generate(
                    **inputs, max_new_tokens=args.max_new_tokens, do_sample=True,
                    temperature=args.temperature, num_return_sequences=args.samples_per_prompt,
                    pad_token_id=tokenizer.pad_token_id,
                )
            completions = []
            for seq in output_ids:
                generated = tokenizer.decode(
                    seq[inputs["input_ids"].shape[1]:], skip_special_tokens=True
                )
                parsed = extract_tool_call_json(generated)
                if parsed is not None:
                    completions.append(parsed)
            del inputs, output_ids
            torch.cuda.empty_cache()

            row_pairs = build_preference_rows(row, completions)
            if not row_pairs:
                skipped_no_negative += 1
            else:
                for pair in row_pairs:
                    out_f.write(json.dumps(pair, ensure_ascii=False) + "\n")
                pairs_written += len(row_pairs)
            out_f.flush()

            if (i + 1) % 10 == 0:
                elapsed = time.time() - t0
                rate = (i + 1) / elapsed
                eta_min = (len(train_rows) - (i + 1)) / rate / 60 if rate > 0 else float("nan")
                print(
                    f"  {i+1}/{len(train_rows)} rows, {pairs_written} pairs so far, "
                    f"{elapsed/60:.1f}min elapsed, ETA {eta_min:.0f}min", flush=True,
                )

    print(f"\n{pairs_written} preference pairs -> {OUTPUT_PATH}", flush=True)
    print(f"{skipped_no_negative} rows skipped (model agreed with gold on every sample)", flush=True)


if __name__ == "__main__":
    main()
