"""is_mandatory / is_text_verifiable accuracy report sections."""
from evaluation.matching import MatchGroup
from evaluation.orchestrator import EvaluationReport
from evaluation.rendering._common import SHORT_ID_LENGTH, collapse_whitespace, percent


def render_flag_group_mismatch(
    group: MatchGroup,
    report: EvaluationReport,
    true_by_topic: dict[str, bool],
    predicted_by_requirement: dict[str, bool],
) -> str:
    topic_id = group.true_topic_ids[0]
    quote = collapse_whitespace(
        report.true_quotes_by_topic.get(topic_id, "(quote unavailable)")
    )
    true_parts = ", ".join(
        f"`{t}`={true_by_topic.get(t)}" for t in group.true_topic_ids
    )
    predicted_parts = ", ".join(
        f"`{r[:SHORT_ID_LENGTH]}`={predicted_by_requirement.get(r)}"
        for r in group.predicted_node_ids
    )
    return (
        f'- true: {true_parts}; predicted: {predicted_parts} — "{quote}"'
    )


def render_flag_mismatches(
    groups: list[MatchGroup],
    report: EvaluationReport,
    true_by_topic: dict[str, bool],
    predicted_by_requirement: dict[str, bool],
) -> list[str]:
    if not groups:
        return ["- none"]
    return [
        render_flag_group_mismatch(
            group, report, true_by_topic, predicted_by_requirement
        )
        for group in groups
    ]


def render_is_mandatory_section(report: EvaluationReport) -> list[str]:
    result = report.is_mandatory_accuracy
    lines = ["## is_mandatory accuracy", ""]
    lines.append(
        "For each clean or one-to-many match (tangled groups excluded — "
        "there's no single \"one\" to compare against), does `is_mandatory` "
        "agree with the true value? A one-to-many group counts as correct "
        "only if every member on the \"many\" side agrees with the \"one\"."
    )
    lines.append("")
    lines.append(
        f"**Accuracy: {percent(result.accuracy)} "
        f"({result.scored_topic_count} groups)**"
    )
    lines.append("")
    lines.append("Mismatched:")
    lines.extend(render_flag_mismatches(
        result.mismatched_groups, report,
        report.is_mandatory_true_by_topic,
        report.is_mandatory_predicted_by_requirement,
    ))
    lines.append("")
    return lines


def render_is_text_verifiable_section(report: EvaluationReport) -> list[str]:
    result = report.is_text_verifiable_accuracy
    lines = ["## is_text_verifiable accuracy", ""]
    lines.append(
        "For each clean or one-to-many match (tangled groups excluded), "
        "does `is_text_verifiable` agree with the true value (all-or-"
        "nothing on the \"many\" side, same rule as is_mandatory above)? "
        "A wrong `false` here means the pipeline skips verdict generation "
        "for a requirement that should get one."
    )
    lines.append("")
    lines.append(
        f"**Accuracy: {percent(result.accuracy)} "
        f"({result.scored_topic_count} groups)**"
    )
    lines.append("")
    lines.append("Mismatched:")
    lines.extend(render_flag_mismatches(
        result.mismatched_groups, report,
        report.is_text_verifiable_true_by_topic,
        report.is_text_verifiable_predicted_by_requirement,
    ))
    lines.append("")
    return lines
