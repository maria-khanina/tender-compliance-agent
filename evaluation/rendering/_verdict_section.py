"""Verdict-accuracy report section: confusion matrix and per-group detail."""
from evaluation.matching import MatchGroup
from evaluation.orchestrator import EvaluationReport
from evaluation.rendering._common import (
    SHORT_ID_LENGTH,
    citation_status_suffix,
    collapse_whitespace,
    percent,
    predicted_line,
    true_line,
    truncate,
)

VERDICT_ORDER = [
    "compliant", "non_compliant", "contradictory", "insufficient_information",
]


def group_for_topic(topic_id: str, groups: list[MatchGroup]) -> MatchGroup | None:
    for group in groups:
        if topic_id in group.true_topic_ids:
            return group
    return None


def confusion_counts(report: EvaluationReport) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], int] = {}
    for cell in report.verdict_accuracy.confusion_matrix:
        counts[(cell.true_verdict, cell.predicted_verdict)] = cell.count
    return counts


def render_confusion_table(counts: dict[tuple[str, str], int]) -> list[str]:
    header = (
        "| true \\ pipeline said | "
        + " | ".join(f"`{v}`" for v in VERDICT_ORDER) + " |"
    )
    separator = "|" + "---|" * (len(VERDICT_ORDER) + 1)
    lines = [header, separator]
    for true_verdict in VERDICT_ORDER:
        row = [
            str(counts.get((true_verdict, predicted), 0))
            for predicted in VERDICT_ORDER
        ]
        lines.append(f"| `{true_verdict}` | " + " | ".join(row) + " |")
    return lines


def row_total(counts: dict[tuple[str, str], int], true_verdict: str) -> int:
    return sum(
        counts.get((true_verdict, predicted), 0) for predicted in VERDICT_ORDER
    )


def topic_absence_reason(topic_id: str, report: EvaluationReport) -> str:
    group = group_for_topic(topic_id, report.match_groups)
    if group is None or group.shape == "unmatched_true":
        return "never extracted (recall miss)"
    if group.shape != "clean":
        return f"{group.shape} match — no single pair to plot"
    requirement_id = group.predicted_node_ids[0]
    if requirement_id not in report.predicted_verdict_labels:
        return "matched, but got no verdict (is_text_verifiable: false)"
    return "scored above"


def render_confusion_gaps(
    counts: dict[tuple[str, str], int],
    report: EvaluationReport,
) -> list[str]:
    empty_labels = [
        label for label in VERDICT_ORDER if row_total(counts, label) == 0
    ]
    lines = []
    for label in empty_labels:
        for topic_id, acceptable in report.acceptable_verdicts_by_topic.items():
            if not acceptable or acceptable[0] != label:
                continue
            reason = topic_absence_reason(topic_id, report)
            if reason == "scored above":
                continue
            lines.append(f"- `{label}` row is empty: true `{topic_id}` — {reason}")
    if not lines:
        return []
    return ["", "Why some rows are empty:"] + lines


def render_combined_verdict_line(
    topic_id: str,
    requirement_id: str,
    report: EvaluationReport,
) -> str:
    acceptable = report.acceptable_verdicts_by_topic.get(topic_id)
    verdict = report.predicted_verdict_labels.get(requirement_id)
    verdict_display = verdict if verdict else "not verifiable by text"
    citation_suffix = citation_status_suffix(requirement_id, report)
    text = report.predicted_texts.get(requirement_id, "(text unavailable)")
    return (
        f"- `{topic_id}` — acceptable: {acceptable}, "
        f'predicted: {verdict_display}{citation_suffix} — '
        f'"{collapse_whitespace(text)}"'
    )


def render_verdict_group(
    group: MatchGroup,
    report: EvaluationReport,
) -> list[str]:
    if len(group.true_topic_ids) == 1 and len(group.predicted_node_ids) == 1:
        topic_id = group.true_topic_ids[0]
        requirement_id = group.predicted_node_ids[0]
        return [render_combined_verdict_line(topic_id, requirement_id, report)]
    lines = []
    for topic_id in group.true_topic_ids:
        acceptable = report.acceptable_verdicts_by_topic.get(topic_id)
        lines.append(
            f"  - {true_line(topic_id, report)} (acceptable: {acceptable})"
        )
    for requirement_id in group.predicted_node_ids:
        lines.append(f"  - {predicted_line(requirement_id, report)}")
    return lines


def render_verdict_group_list(
    groups: list[MatchGroup],
    report: EvaluationReport,
) -> list[str]:
    if not groups:
        return ["- none"]
    lines = []
    for index, group in enumerate(groups, start=1):
        rendered = render_verdict_group(group, report)
        if len(rendered) == 1:
            lines.append(rendered[0])
        else:
            lines.append(f"- group {index}:")
            lines.extend(rendered)
    return lines


def render_verdict_header_line(
    topic_id: str,
    requirement_id: str,
    report: EvaluationReport,
) -> str:
    acceptable = report.acceptable_verdicts_by_topic.get(topic_id)
    verdict = report.predicted_verdict_labels.get(requirement_id)
    verdict_display = verdict if verdict else "not verifiable by text"
    citation_suffix = citation_status_suffix(requirement_id, report)
    return (
        f"- `{topic_id}` — acceptable: {acceptable}, "
        f"predicted: {verdict_display}{citation_suffix}"
    )


def render_model_detail_lines(
    requirement_id: str,
    report: EvaluationReport,
) -> list[str]:
    text = collapse_whitespace(
        report.predicted_texts.get(requirement_id, "(text unavailable)")
    )
    retrieved_chunks = report.retrieved_context_by_requirement.get(
        requirement_id, []
    )
    evidence_quotes = report.predicted_verdict_evidence.get(requirement_id, [])
    reasoning = report.predicted_verdict_reasoning.get(requirement_id, "")
    lines = [f'  - **requirement:** "{text}"']
    if not retrieved_chunks:
        lines.append("  - **retrieved context (shown to the model):** none")
    for chunk_text in retrieved_chunks:
        lines.append(
            f'  - **retrieved context (shown to the model):** '
            f'"{truncate(collapse_whitespace(chunk_text))}"'
        )
    if not evidence_quotes:
        lines.append("  - **model's evidence (what it chose to cite):** none")
    for quote in evidence_quotes:
        lines.append(
            f"  - **model's evidence (what it chose to cite):** "
            f'"{collapse_whitespace(quote)}"'
        )
    if reasoning:
        lines.append(
            f"  - **model's reasoning:** {collapse_whitespace(reasoning)}"
        )
    return lines


def render_expected_detail_lines(
    topic_id: str,
    report: EvaluationReport,
) -> list[str]:
    evidence_quotes = report.true_evidence_by_topic.get(topic_id, [])
    rationale = report.true_verdict_rationale_by_topic.get(topic_id, "")
    lines = []
    if not evidence_quotes:
        lines.append("  - **expected evidence (true_verdicts.json):** none")
    for quote in evidence_quotes:
        lines.append(
            f'  - **expected evidence (true_verdicts.json):** '
            f'"{collapse_whitespace(quote)}"'
        )
    if rationale:
        lines.append(
            f"  - **expected reasoning:** {collapse_whitespace(rationale)}"
        )
    return lines


def render_group_retrieved_context(
    requirement_ids: list[str],
    report: EvaluationReport,
) -> list[str]:
    seen_chunks: set[str] = set()
    lines = []
    for requirement_id in requirement_ids:
        chunks = report.retrieved_context_by_requirement.get(requirement_id, [])
        for chunk_text in chunks:
            truncated = truncate(collapse_whitespace(chunk_text))
            if truncated in seen_chunks:
                continue
            seen_chunks.add(truncated)
            lines.append(
                f'  - **retrieved context (shown to the model):** '
                f'"{truncated}"'
            )
    if not lines:
        lines.append("  - **retrieved context (shown to the model):** none")
    return lines


def render_predicted_verdict_lines(
    requirement_id: str,
    report: EvaluationReport,
) -> list[str]:
    evidence_quotes = report.predicted_verdict_evidence.get(requirement_id, [])
    reasoning = report.predicted_verdict_reasoning.get(requirement_id, "")
    lines = [f"    - {predicted_line(requirement_id, report)}"]
    if not evidence_quotes:
        lines.append("      - **model's evidence (what it chose to cite):** none")
    for quote in evidence_quotes:
        lines.append(
            f"      - **model's evidence (what it chose to cite):** "
            f'"{collapse_whitespace(quote)}"'
        )
    if reasoning:
        lines.append(
            f"      - **model's reasoning:** {collapse_whitespace(reasoning)}"
        )
    return lines


def render_verdict_group_with_detail(
    group: MatchGroup,
    report: EvaluationReport,
) -> list[str]:
    if len(group.true_topic_ids) == 1 and len(group.predicted_node_ids) == 1:
        topic_id = group.true_topic_ids[0]
        requirement_id = group.predicted_node_ids[0]
        lines = [render_verdict_header_line(topic_id, requirement_id, report)]
        lines.extend(render_model_detail_lines(requirement_id, report))
        lines.extend(render_expected_detail_lines(topic_id, report))
        return lines
    lines = [
        f"- group of {len(group.true_topic_ids)} true topic(s) and "
        f"{len(group.predicted_node_ids)} predicted requirement(s) "
        "(not a 1:1 match, so there is no single correct pairing between "
        "them):",
    ]
    for topic_id in group.true_topic_ids:
        acceptable = report.acceptable_verdicts_by_topic.get(topic_id)
        lines.append(
            f"  - {true_line(topic_id, report)} (acceptable: {acceptable})"
        )
        lines.extend(
            f"    {line}" for line in render_expected_detail_lines(
                topic_id, report
            )
        )
    lines.extend(
        render_group_retrieved_context(group.predicted_node_ids, report)
    )
    lines.append("  - predicted verdicts in this group:")
    for requirement_id in group.predicted_node_ids:
        lines.extend(render_predicted_verdict_lines(requirement_id, report))
    return lines


def render_verdict_group_list_with_detail(
    groups: list[MatchGroup],
    report: EvaluationReport,
) -> list[str]:
    if not groups:
        return ["- none"]
    lines = []
    for group in groups:
        lines.extend(render_verdict_group_with_detail(group, report))
        lines.append("")
    return lines[:-1]


def render_verdict_section(report: EvaluationReport) -> list[str]:
    result = report.verdict_accuracy
    lines = ["## Verdict accuracy", ""]
    lines.append(
        "The confusion matrix covers only clean 1:1 matches — split/merge "
        "groups have no single pair to plot, but still count in the two "
        "rates below."
    )
    lines.append("")
    lines.append(f"Clean matches scored: {result.clean_match_count}")
    lines.append("")
    counts = confusion_counts(report)
    lines.extend(render_confusion_table(counts))
    lines.extend(render_confusion_gaps(counts, report))
    lines.append("")
    lines.append(
        "**Mismatched clean matches** — every off-diagonal cell above, in "
        "full: the full context retrieved and shown to the model, what it "
        "chose to cite from that context, and its reasoning (\"model's "
        "...\"), next to what `true_verdicts.json` expects (\"expected "
        "...\")."
    )
    lines.append("")
    lines.extend(
        render_verdict_group_list_with_detail(
            result.mismatched_clean_groups, report
        )
    )
    lines.append("")
    lines.append(
        "**False-compliant rate** — dangerous direction: the true verdict "
        "requires an issue (anything but `compliant`), but every predicted "
        "verdict in the group is `compliant`."
    )
    lines.append(f"- rate: {percent(result.false_compliant_rate)}")
    lines.append("")
    lines.extend(
        render_verdict_group_list_with_detail(
            result.false_compliant_groups, report
        )
    )
    lines.append("")
    lines.append(
        "**False-issue rate** — mirror direction: the true verdict is "
        "`compliant` only, but the pipeline raised an issue anyway."
    )
    lines.append(f"- rate: {percent(result.false_issue_rate)}")
    lines.append("")
    lines.extend(
        render_verdict_group_list_with_detail(
            result.false_issue_groups, report
        )
    )
    lines.append("")
    lines.append(
        "**Unscored** — split/merge groups excluded from the matrix above "
        "(still counted in the two rates above):"
    )
    lines.extend(render_verdict_group_list(result.unscored_groups, report))
    lines.append("")
    lines.append(
        "**Not applicable** — the requirement's applicability condition "
        "was judged not to hold for this bidder, so its verdict is "
        "excluded from every metric above; see \"Applicability "
        "conditions\" below for whether that judgment was correct."
    )
    lines.extend(
        render_verdict_group_list(result.not_applicable_groups, report)
    )
    lines.append("")
    return lines
