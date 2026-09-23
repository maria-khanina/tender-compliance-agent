"""Applicability-condition detection and condition_holds accuracy section."""
from evaluation.orchestrator import EvaluationReport
from evaluation.rendering._common import percent, true_line
from evaluation.rendering._flag_accuracy_sections import render_flag_mismatches


def render_condition_section(report: EvaluationReport) -> list[str]:
    detection = report.applicability_condition_detection
    holds = report.condition_holds_accuracy
    lines = ["## Applicability conditions", ""]
    lines.append(
        "For requirements whose applicability itself depends on a fact "
        "about the bidder (\"if offering an equal product...\"), two "
        "separate questions: did the pipeline find the right clause "
        "stating the condition, and did it correctly judge whether the "
        "condition holds for this bidder."
    )
    lines.append("")
    lines.append(
        f"**Condition detection recall: {percent(detection.detection_recall)} "
        f"({detection.detected_topic_count}/"
        f"{detection.true_condition_topic_count})** — of the true "
        "topics with a stated condition, how many the pipeline also "
        "flagged as conditional, with an overlapping citation."
    )
    lines.append("- missed:")
    if not detection.missed_condition_topic_ids:
        lines.append("  - none")
    for topic_id in detection.missed_condition_topic_ids:
        lines.append(f"  - {true_line(topic_id, report)}")
    lines.append(
        f"- false positives (flagged conditional, true topic is not): "
        f"{len(detection.false_condition_requirement_ids)}"
    )
    lines.append("")
    lines.append(
        f"**condition_holds accuracy: {percent(holds.accuracy)} "
        f"({holds.scored_topic_count} topics)** — of the topics with a "
        "confirmed condition, did the pipeline correctly judge whether "
        "it holds for this bidder:"
    )
    lines.extend(render_flag_mismatches(
        holds.mismatched_groups, report,
        report.condition_holds_true_by_topic,
        report.condition_holds_predicted_by_requirement,
    ))
    lines.append("")
    return lines
