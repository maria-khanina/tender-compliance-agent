"""Machine-readable summary metrics report section."""
import json

from evaluation.orchestrator import EvaluationReport
from evaluation.verdict_metrics import VerdictAccuracyResult


def verdict_accuracy_ratio(result: VerdictAccuracyResult) -> float | None:
    if result.clean_match_count <= 0:
        return None
    correct = result.clean_match_count - len(result.mismatched_clean_groups)
    return correct / result.clean_match_count


def round_or_none(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 4)


def build_summary_metrics(
    report: EvaluationReport,
    verdict_only_accuracy: float | None = None,
    verdict_only_scored: int | None = None,
) -> dict[str, float | int | None]:
    return {
        "requirement_recall": round(report.requirement_recall.recall, 4),
        "requirement_recall_matched": (
            report.requirement_recall.matched_topic_count
        ),
        "requirement_recall_total": (
            report.requirement_recall.total_topic_count
        ),
        "requirement_precision": round(
            report.requirement_precision.classification_precision, 4
        ),
        "citation_verified_rate": round(
            report.requirement_precision.citation_verified_rate, 4
        ),
        "is_mandatory_accuracy": round(
            report.is_mandatory_accuracy.accuracy, 4
        ),
        "is_mandatory_scored": (
            report.is_mandatory_accuracy.scored_topic_count
        ),
        "is_text_verifiable_accuracy": round(
            report.is_text_verifiable_accuracy.accuracy, 4
        ),
        "is_text_verifiable_scored": (
            report.is_text_verifiable_accuracy.scored_topic_count
        ),
        "verdict_clean_match_count": (
            report.verdict_accuracy.clean_match_count
        ),
        "verdict_accuracy": round_or_none(
            verdict_accuracy_ratio(report.verdict_accuracy)
        ),
        "false_compliant_rate": round(
            report.verdict_accuracy.false_compliant_rate, 4
        ),
        "false_issue_rate": round(
            report.verdict_accuracy.false_issue_rate, 4
        ),
        "evidence_hallucination_rate": round(
            report.evidence_hallucination.hallucination_rate, 4
        ),
        "context_recall": round(report.context_recall.recall, 4),
        "verdict_only_accuracy": round_or_none(verdict_only_accuracy),
        "verdict_only_scored": verdict_only_scored,
    }


def render_metrics_summary_lines(
    report: EvaluationReport,
    verdict_only_accuracy: float | None = None,
    verdict_only_scored: int | None = None,
) -> list[str]:
    metrics = build_summary_metrics(
        report, verdict_only_accuracy, verdict_only_scored
    )
    lines = ["## Summary metrics", ""]
    lines.append(
        "Machine-readable numbers for averaging across tenders -- every "
        "value here is explained in the sections below. `null` means "
        "the metric doesn't apply to this run (e.g. no verdict-only "
        "artifact present)."
    )
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(metrics, indent=2))
    lines.append("```")
    lines.append("")
    return lines
