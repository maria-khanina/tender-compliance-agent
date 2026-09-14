"""Run scripts/evaluate_verdicts.py across a set of cases against a given
LLM endpoint, WITHOUT touching the shared .env file -- provider/base_url/
model/api_key are passed as environment variable overrides to a
subprocess, which take precedence over .env (pydantic-settings) for that
process only. Safe to run alongside other sessions using Gemini via the
real .env.

Usage:
  python sft/run_verdict_eval.py --label baseline-qwen3-8b-awq --cases val test
  python sft/run_verdict_eval.py --label sft-lora-step160 --cases val test \
      --model Qwen/Qwen3-8B-AWQ  # (served with the LoRA adapter loaded)
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys

sys.path.insert(0, r"C:\Users\Grani\Desktop\lapka\maria.khanina\NLP\agents\tender_agent")
os.chdir(r"C:\Users\Grani\Desktop\lapka\maria.khanina\NLP\agents\tender_agent")

SPLIT_CONFIG = json.load(open("sft/split.json", encoding="utf-8"))


def cases_for(selection: list[str]) -> list[str]:
    all_cases = sorted(
        os.path.basename(d) for d in __import__("glob").glob("data/*")
        if os.path.isdir(d) and os.path.exists(os.path.join(d, "true_verdicts.json"))
    )
    test = set(SPLIT_CONFIG["test"])
    val = set(SPLIT_CONFIG["validation"])
    chosen = []
    for s in selection:
        if s == "test":
            chosen.extend(sorted(test))
        elif s in ("val", "validation"):
            chosen.extend(sorted(val))
        elif s == "train":
            chosen.extend(sorted(c for c in all_cases if c not in test and c not in val))
        elif s == "all":
            chosen.extend(all_cases)
        else:
            chosen.append(s)
    seen = set()
    result = []
    for c in chosen:
        if c not in seen:
            seen.add(c)
            result.append(c)
    return result


def run_one_case(case: str, label: str, base_url: str, model: str) -> dict:
    case_dir = f"data/{case}"
    out_dir = f"sft/eval_runs/{label}"
    os.makedirs(out_dir, exist_ok=True)
    report_path = f"{out_dir}/{case}.md"

    env = os.environ.copy()
    env["LANGUAGE_MODEL_PROVIDER"] = "openai_compatible"
    env["LANGUAGE_MODEL_BASE_URL"] = base_url
    env["LANGUAGE_MODEL_NAME"] = model
    env["LANGUAGE_MODEL_API_KEY"] = "not-needed"

    result = subprocess.run(
        [
            sys.executable, "scripts/evaluate_verdicts.py",
            "--case-dir", case_dir,
            "--report-output", report_path,
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    ok = result.returncode == 0
    accuracy = None
    if ok:
        verdicts_path = pathlib.Path(case_dir) / "verdict_only_verdicts.json"
        # accuracy is embedded in the printed report; re-derive from the
        # saved artifact + fixture directly so we don't need to parse markdown
        from evaluation.fixtures import load_true_verdicts
        from evaluation.verdict_only import build_synthetic_requirements, score_verdicts
        from evaluation.fixtures import load_true_requirements, load_retrieved_evidence, load_predicted_verdicts
        try:
            true_verdicts = load_true_verdicts(pathlib.Path(case_dir) / "true_verdicts.json")
            predicted = load_predicted_verdicts(verdicts_path)
            retrieved = load_retrieved_evidence(
                pathlib.Path(case_dir) / "verdict_only_retrieved_evidence.json"
            )
            scored = score_verdicts(predicted, true_verdicts, retrieved)
            accuracy = scored.accuracy
        except Exception as e:
            accuracy = None
            ok = False
            result_stderr = str(e)
    return {
        "case": case,
        "ok": ok,
        "returncode": result.returncode,
        "accuracy": accuracy,
        "stderr_tail": result.stderr[-2000:] if not ok else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--cases", nargs="+", default=["val", "test"])
    parser.add_argument("--base-url", default="http://localhost:8000/v1")
    parser.add_argument("--model", default="Qwen/Qwen3-8B-AWQ")
    parser.add_argument(
        "--resume", action="store_true",
        help="Skip cases that already have a successful result in this "
             "label's summary.json (so a mid-run vLLM crash only costs the "
             "one case that was in flight, not the whole run).",
    )
    args = parser.parse_args()

    cases = cases_for(args.cases)
    out_dir = f"sft/eval_runs/{args.label}"
    os.makedirs(out_dir, exist_ok=True)
    summary_path = f"{out_dir}/summary.json"

    results = []
    done_cases = set()
    if args.resume and os.path.exists(summary_path):
        with open(summary_path, encoding="utf-8") as f:
            prior = json.load(f)
        for r in prior.get("results", []):
            if r["ok"] and r["accuracy"] is not None:
                results.append(r)
                done_cases.add(r["case"])
        print(f"Resuming: {len(done_cases)} case(s) already succeeded, skipping them.")

    print(f"Running verdict eval (label={args.label}) on: {cases}")

    for case in cases:
        if case in done_cases:
            print(f"  -> {case} ... skipped (already succeeded)")
            continue
        print(f"  -> {case} ...", flush=True)
        r = run_one_case(case, args.label, args.base_url, args.model)
        results.append(r)
        status = f"accuracy={r['accuracy']:.3f}" if r["accuracy"] is not None else "FAILED"
        print(f"     {status}", flush=True)
        if not r["ok"]:
            print(f"     stderr tail:\n{r['stderr_tail']}", flush=True)
        # Persist after every case, not just at the end -- a vLLM crash
        # mid-run should only cost the in-flight case's result, not every
        # case that already finished successfully before it.
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump({"label": args.label, "model": args.model, "results": results}, f, indent=2)

    ok_results = [r for r in results if r["ok"] and r["accuracy"] is not None]
    if ok_results:
        avg = sum(r["accuracy"] for r in ok_results) / len(ok_results)
        print(f"\nAverage accuracy across {len(ok_results)}/{len(results)} cases: {avg:.3f}")
    else:
        print("\nNo successful runs.")


if __name__ == "__main__":
    main()
