"""Coverage-flag report section (partial-citation-overlap matches)."""
from config import EVALUATION_COVERAGE_FLAG_THRESHOLD
from evaluation.orchestrator import EvaluationReport
from evaluation.rendering._common import (
    SHORT_ID_LENGTH,
    collapse_whitespace,
    percent,
)
from evaluation.requirement_metrics import CoverageFlag


def flag_true_quotes(flag: CoverageFlag, report: EvaluationReport) -> str:
    quotes = [
        collapse_whitespace(
            report.true_quotes_by_topic.get(topic_id, "(quote unavailable)")
        )
        for topic_id in flag.true_topic_ids
    ]
    return "; ".join(f'"{quote}"' for quote in quotes)


def render_coverage_group(
    flag: CoverageFlag,
    report: EvaluationReport,
    percent_value: float,
    contained_is_predicted: bool,
) -> list[str]:
    true_topics = ", ".join(f"`{t}`" for t in flag.true_topic_ids)
    true_quotes = flag_true_quotes(flag, report)
    lines = []
    for requirement_id in flag.predicted_node_ids:
        text = collapse_whitespace(
            report.predicted_texts.get(requirement_id, "(text unavailable)")
        )
        short_id = requirement_id[:SHORT_ID_LENGTH]
        if contained_is_predicted:
            lines.append(
                f"- predicted [{short_id}] is contained in true "
                f"{true_topics} — {percent(percent_value)}:"
            )
        else:
            lines.append(
                f"- true {true_topics} is contained in predicted "
                f"[{short_id}] — {percent(percent_value)}:"
            )
        lines.append(f'    predicted: "{text}"')
        lines.append(f"    true: {true_quotes}")
        lines.append("")
    return lines


def render_coverage_section(report: EvaluationReport) -> list[str]:
    flags = report.coverage_flags
    lines = ["## Coverage flags", ""]
    lines.append(
        "Clean 1:1 matches (recall counted them as found) whose citations "
        "don't fully overlap in length, split by which side is off. "
        "Over-split/over-merge/tangled matches are excluded here -- their "
        "predicted fragments are inherently partial by construction, "
        "already shown in the recall breakdown above."
    )
    lines.append("")
    extra_text_flags = [
        flag for flag in flags
        if flag.predicted_explained_ratio < EVALUATION_COVERAGE_FLAG_THRESHOLD
    ]
    incomplete_flags = [
        flag for flag in flags
        if flag.true_covered_ratio < EVALUATION_COVERAGE_FLAG_THRESHOLD
    ]
    lines.append(
        f"**Requirements captured with extra text** ({len(extra_text_flags)}) "
        "— the predicted citation is padded beyond the true one:"
    )
    if not extra_text_flags:
        lines.append("- none")
    for flag in extra_text_flags:
        lines.extend(render_coverage_group(
            flag, report, flag.predicted_explained_ratio,
            contained_is_predicted=False,
        ))
    if extra_text_flags:
        lines.pop()
    lines.append("")
    lines.append(
        f"**Requirements captured incompletely** ({len(incomplete_flags)}) "
        "— the predicted citation misses part of the true one:"
    )
    if not incomplete_flags:
        lines.append("- none")
    for flag in incomplete_flags:
        lines.extend(render_coverage_group(
            flag, report, flag.true_covered_ratio,
            contained_is_predicted=True,
        ))
    if incomplete_flags:
        lines.pop()
    lines.append("")
    return lines
