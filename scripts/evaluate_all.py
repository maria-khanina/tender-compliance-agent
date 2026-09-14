"""Run all three evaluation stages for a case and print/save a combined
picture: full-pipeline (extraction + verdict, scripts/evaluate.py),
verdict-only (scripts/evaluate_verdicts.py), and retrieval-only
(scripts/evaluate_retrieval.py). This is what "запусти evaluation" should
mean -- one command, the whole picture, not three separately-remembered
invocations.

Usage:
  python scripts/evaluate_all.py --case-dir data/36C24126Q0704

Each stage writes its own report as usual (evaluation_report.md,
verdict_only_report.md, retrieval_only_report.md in the case dir unless
--report-dir is given) plus this prints a short combined summary.
"""
import argparse
import pathlib
import subprocess
import sys


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", required=True)
    parser.add_argument(
        "--report-dir",
        help="Directory to write the three *_report.md files into "
             "(default: the case dir itself, matching each script's own "
             "default naming).",
    )
    parser.add_argument(
        "--skip",
        nargs="*",
        default=[],
        choices=["pipeline", "verdict", "retrieval"],
        help="Stage(s) to skip, e.g. --skip pipeline if predicted_*.json "
             "isn't available for this case yet.",
    )
    return parser.parse_args()


def _run(script: str, case_dir: str, report_path: str) -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, script, "--case-dir", case_dir,
         "--report-output", report_path],
        capture_output=True, text=True,
    )
    return result.returncode == 0, (result.stdout + result.stderr)


def main() -> None:
    args = _parse_arguments()
    case_dir = args.case_dir
    report_dir = pathlib.Path(args.report_dir) if args.report_dir else pathlib.Path(case_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    stages = [
        ("pipeline", "scripts/evaluate.py", str(report_dir / "evaluation_report.md")),
        ("verdict", "scripts/evaluate_verdicts.py", str(report_dir / "verdict_only_report.md")),
        ("retrieval", "scripts/evaluate_retrieval.py", str(report_dir / "retrieval_only_report.md")),
    ]

    print(f"=== evaluate_all: {case_dir} ===\n")
    for name, script, report_path in stages:
        if name in args.skip:
            print(f"[{name}] skipped")
            continue
        ok, output = _run(script, case_dir, report_path)
        status = "ok" if ok else "FAILED"
        print(f"[{name}] {status} -> {report_path}")
        if not ok:
            print(output[-2000:])
        else:
            # surface just the headline numbers, not the full report
            for line in output.splitlines():
                if line.strip().startswith("**") or "accuracy" in line.lower() or "recall" in line.lower():
                    print(f"    {line.strip()}")
    print(f"\nFull reports written under {report_dir}")


if __name__ == "__main__":
    main()
