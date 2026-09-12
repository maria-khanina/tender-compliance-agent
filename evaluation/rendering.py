import json

from config import EVALUATION_COVERAGE_FLAG_THRESHOLD
from evaluation.matching import MatchGroup
from evaluation.orchestrator import EvaluationReport
from evaluation.requirement_metrics import CoverageFlag
from evaluation.verdict_metrics import VerdictAccuracyResult


PERCENT_SCALE = 100.0
SHORT_ID_LENGTH = 8
VERDICT_ORDER = [
    "compliant", "non_compliant", "contradictory", "insufficient_information",
]


def _percent(ratio: float) -> str:
    return f"{ratio * PERCENT_SCALE:.1f}%"


def _collapse_whitespace(text: str) -> str:
    return " ".join(text.split())


def _true_line(topic_id: str, report: EvaluationReport) -> str:
    quote = report.true_quotes_by_topic.get(topic_id, "(quote unavailable)")
    return f'true `{topic_id}` — "{_collapse_whitespace(quote)}"'


def _citation_status_suffix(requirement_id: str, report: EvaluationReport) -> str:
    status = report.predicted_citation_status.get(requirement_id, "precise")
    if status == "unverified":
        return ", citation: UNVERIFIED — not located in tender.txt"
    if status == "fuzzy":
        return ", citation: fuzzy match — worth a second look"
    return ""


def _predicted_text_line(requirement_id: str, report: EvaluationReport) -> str:
    text = report.predicted_texts.get(requirement_id, "(text unavailable)")
    short_id = requirement_id[:SHORT_ID_LENGTH]
    return f'predicted [{short_id}] "{_collapse_whitespace(text)}"'


def _predicted_line(requirement_id: str, report: EvaluationReport) -> str:
    verdict = report.predicted_verdict_labels.get(requirement_id)
    if verdict:
        verdict_suffix = f" — verdict: {verdict}"
    else:
        verdict_suffix = " — not verifiable by text"
    citation_suffix = _citation_status_suffix(requirement_id, report)
    return (
        f"{_predicted_text_line(requirement_id, report)}"
        f"{verdict_suffix}{citation_suffix}"
    )


def _groups_by_shape(
    groups: list[MatchGroup],
) -> dict[str, list[MatchGroup]]:
    grouped: dict[str, list[MatchGroup]] = {}
    for group in groups:
        grouped.setdefault(group.shape, []).append(group)
    return grouped


def _group_for_topic(
    topic_id: str,
    groups: list[MatchGroup],
) -> MatchGroup | None:
    for group in groups:
        if topic_id in group.true_topic_ids:
            return group
    return None


def _render_missed(
    groups: list[MatchGroup],
    report: EvaluationReport,
) -> list[str]:
    if not groups:
        return ["- none"]
    lines = []
    for group in groups:
        for topic_id in group.true_topic_ids:
            lines.append(f"- {_true_line(topic_id, report)}")
    return lines


def _render_over_split(
    groups: list[MatchGroup],
    report: EvaluationReport,
) -> list[str]:
    if not groups:
        return ["- none"]
    lines = []
    for group in groups:
        topic_id = group.true_topic_ids[0]
        lines.append(
            f"- {_true_line(topic_id, report)} split into "
            f"{len(group.predicted_node_ids)} predicted requirements:"
        )
        for requirement_id in group.predicted_node_ids:
            lines.append(f"  - {_predicted_line(requirement_id, report)}")
    return lines


def _render_over_merge(
    groups: list[MatchGroup],
    report: EvaluationReport,
) -> list[str]:
    if not groups:
        return ["- none"]
    lines = []
    for group in groups:
        requirement_id = group.predicted_node_ids[0]
        lines.append(
            f"- {_predicted_line(requirement_id, report)} lumps together "
            f"{len(group.true_topic_ids)} true requirements:"
        )
        for topic_id in group.true_topic_ids:
            lines.append(f"  - {_true_line(topic_id, report)}")
    return lines


def _render_tangled(
    groups: list[MatchGroup],
    report: EvaluationReport,
) -> list[str]:
    if not groups:
        return ["- none"]
    lines = []
    for group in groups:
        lines.append(
            f"- tangle of {len(group.true_topic_ids)} true and "
            f"{len(group.predicted_node_ids)} predicted requirements, all "
            "overlapping — needs manual untangling:"
        )
        for topic_id in group.true_topic_ids:
            lines.append(f"  - {_true_line(topic_id, report)}")
        for requirement_id in group.predicted_node_ids:
            lines.append(f"  - {_predicted_line(requirement_id, report)}")
    return lines


def _render_recall_section(report: EvaluationReport) -> list[str]:
    result = report.requirement_recall
    by_shape = _groups_by_shape(report.match_groups)
    lines = ["## Requirement recall", ""]
    lines.append(
        "For each `true_requirements.json` topic, did the pipeline extract "
        "something whose tender.txt citation overlaps the true one? A pure "
        "text-offset check, not a judgment of meaning — see coverage flags "
        "below for extractions that are technically \"found\" but sloppy."
    )
    lines.append("")
    lines.append(
        f"**Recall: {_percent(result.recall)} "
        f"({result.matched_topic_count}/{result.total_topic_count})**"
    )
    lines.append("")
    lines.append(
        f"**Missed** ({len(by_shape.get('unmatched_true', []))}) — no "
        "overlapping predicted requirement at all:"
    )
    lines.extend(_render_missed(by_shape.get("unmatched_true", []), report))
    lines.append("")
    lines.append(
        f"**Over-split** ({len(by_shape.get('over_split', []))}) — one "
        "true topic extracted as several separate predicted requirements:"
    )
    lines.extend(_render_over_split(by_shape.get("over_split", []), report))
    lines.append("")
    lines.append(
        f"**Over-merge** ({len(by_shape.get('over_merge', []))}) — one "
        "predicted requirement covering several distinct true topics:"
    )
    lines.extend(_render_over_merge(by_shape.get("over_merge", []), report))
    lines.append("")
    lines.append(
        f"**Tangled** ({len(by_shape.get('tangled', []))}) — several true "
        "and several predicted requirements all overlapping at once:"
    )
    lines.extend(_render_tangled(by_shape.get("tangled", []), report))
    lines.append("")
    return lines


def _render_precision_section(report: EvaluationReport) -> list[str]:
    result = report.requirement_precision
    lines = ["## Requirement precision", ""]
    lines.append(
        "**Citation-verified rate** (hallucination check): fraction of "
        "predicted requirements whose citation was actually located in "
        "tender.txt (exactly or via fuzzy match)."
    )
    lines.append(f"- rate: {_percent(result.citation_verified_rate)}")
    lines.append("- unverified:")
    if not result.unverified_requirement_ids:
        lines.append("  - none")
    for requirement_id in result.unverified_requirement_ids:
        lines.append(f"  - {_predicted_line(requirement_id, report)}")
    lines.append("")
    lines.append(
        "**Classification precision**: fraction of predicted requirements "
        "that matched a true requirement."
    )
    lines.append(f"- rate: {_percent(result.classification_precision)}")
    lines.append(
        f"- unexplained ({len(result.unexplained_requirement_ids)}) — "
        "the model recognized these as requirements, but they don't match "
        "any true requirement:"
    )
    if not result.unexplained_requirement_ids:
        lines.append("  - none")
    for requirement_id in result.unexplained_requirement_ids:
        lines.append(f"  - {_predicted_text_line(requirement_id, report)}")
    lines.append("")
    return lines


def _flag_true_quotes(flag: CoverageFlag, report: EvaluationReport) -> str:
    quotes = [
        _collapse_whitespace(
            report.true_quotes_by_topic.get(topic_id, "(quote unavailable)")
        )
        for topic_id in flag.true_topic_ids
    ]
    return "; ".join(f'"{quote}"' for quote in quotes)


def _render_coverage_group(
    flag: CoverageFlag,
    report: EvaluationReport,
    percent_value: float,
    contained_is_predicted: bool,
) -> list[str]:
    true_topics = ", ".join(f"`{t}`" for t in flag.true_topic_ids)
    true_quotes = _flag_true_quotes(flag, report)
    lines = []
    for requirement_id in flag.predicted_node_ids:
        text = _collapse_whitespace(
            report.predicted_texts.get(requirement_id, "(text unavailable)")
        )
        short_id = requirement_id[:SHORT_ID_LENGTH]
        if contained_is_predicted:
            lines.append(
                f"- predicted [{short_id}] is contained in true "
                f"{true_topics} — {_percent(percent_value)}:"
            )
        else:
            lines.append(
                f"- true {true_topics} is contained in predicted "
                f"[{short_id}] — {_percent(percent_value)}:"
            )
        lines.append(f'    predicted: "{text}"')
        lines.append(f"    true: {true_quotes}")
        lines.append("")
    return lines


def _render_coverage_section(report: EvaluationReport) -> list[str]:
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
        lines.extend(_render_coverage_group(
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
        lines.extend(_render_coverage_group(
            flag, report, flag.true_covered_ratio,
            contained_is_predicted=True,
        ))
    if incomplete_flags:
        lines.pop()
    lines.append("")
    return lines


def _render_flag_group_mismatch(
    group: MatchGroup,
    report: EvaluationReport,
    true_by_topic: dict[str, bool],
    predicted_by_requirement: dict[str, bool],
) -> str:
    topic_id = group.true_topic_ids[0]
    quote = _collapse_whitespace(
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


def _render_flag_mismatches(
    groups: list[MatchGroup],
    report: EvaluationReport,
    true_by_topic: dict[str, bool],
    predicted_by_requirement: dict[str, bool],
) -> list[str]:
    if not groups:
        return ["- none"]
    return [
        _render_flag_group_mismatch(
            group, report, true_by_topic, predicted_by_requirement
        )
        for group in groups
    ]


def _render_is_mandatory_section(report: EvaluationReport) -> list[str]:
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
        f"**Accuracy: {_percent(result.accuracy)} "
        f"({result.scored_topic_count} groups)**"
    )
    lines.append("")
    lines.append("Mismatched:")
    lines.extend(_render_flag_mismatches(
        result.mismatched_groups, report,
        report.is_mandatory_true_by_topic,
        report.is_mandatory_predicted_by_requirement,
    ))
    lines.append("")
    return lines


def _render_is_text_verifiable_section(report: EvaluationReport) -> list[str]:
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
        f"**Accuracy: {_percent(result.accuracy)} "
        f"({result.scored_topic_count} groups)**"
    )
    lines.append("")
    lines.append("Mismatched:")
    lines.extend(_render_flag_mismatches(
        result.mismatched_groups, report,
        report.is_text_verifiable_true_by_topic,
        report.is_text_verifiable_predicted_by_requirement,
    ))
    lines.append("")
    return lines


def _confusion_counts(report: EvaluationReport) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], int] = {}
    for cell in report.verdict_accuracy.confusion_matrix:
        counts[(cell.true_verdict, cell.predicted_verdict)] = cell.count
    return counts


def _render_confusion_table(counts: dict[tuple[str, str], int]) -> list[str]:
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


def _row_total(counts: dict[tuple[str, str], int], true_verdict: str) -> int:
    return sum(
        counts.get((true_verdict, predicted), 0) for predicted in VERDICT_ORDER
    )


def _topic_absence_reason(topic_id: str, report: EvaluationReport) -> str:
    group = _group_for_topic(topic_id, report.match_groups)
    if group is None or group.shape == "unmatched_true":
        return "never extracted (recall miss)"
    if group.shape != "clean":
        return f"{group.shape} match — no single pair to plot"
    requirement_id = group.predicted_node_ids[0]
    if requirement_id not in report.predicted_verdict_labels:
        return "matched, but got no verdict (is_text_verifiable: false)"
    return "scored above"


def _render_confusion_gaps(
    counts: dict[tuple[str, str], int],
    report: EvaluationReport,
) -> list[str]:
    empty_labels = [
        label for label in VERDICT_ORDER if _row_total(counts, label) == 0
    ]
    lines = []
    for label in empty_labels:
        for topic_id, acceptable in report.acceptable_verdicts_by_topic.items():
            if not acceptable or acceptable[0] != label:
                continue
            reason = _topic_absence_reason(topic_id, report)
            if reason == "scored above":
                continue
            lines.append(f"- `{label}` row is empty: true `{topic_id}` — {reason}")
    if not lines:
        return []
    return ["", "Why some rows are empty:"] + lines


def _render_combined_verdict_line(
    topic_id: str,
    requirement_id: str,
    report: EvaluationReport,
) -> str:
    acceptable = report.acceptable_verdicts_by_topic.get(topic_id)
    verdict = report.predicted_verdict_labels.get(requirement_id)
    verdict_display = verdict if verdict else "not verifiable by text"
    citation_suffix = _citation_status_suffix(requirement_id, report)
    text = report.predicted_texts.get(requirement_id, "(text unavailable)")
    return (
        f"- `{topic_id}` — acceptable: {acceptable}, "
        f'predicted: {verdict_display}{citation_suffix} — '
        f'"{_collapse_whitespace(text)}"'
    )


def _render_verdict_group(
    group: MatchGroup,
    report: EvaluationReport,
) -> list[str]:
    if len(group.true_topic_ids) == 1 and len(group.predicted_node_ids) == 1:
        topic_id = group.true_topic_ids[0]
        requirement_id = group.predicted_node_ids[0]
        return [_render_combined_verdict_line(topic_id, requirement_id, report)]
    lines = []
    for topic_id in group.true_topic_ids:
        acceptable = report.acceptable_verdicts_by_topic.get(topic_id)
        lines.append(
            f"  - {_true_line(topic_id, report)} (acceptable: {acceptable})"
        )
    for requirement_id in group.predicted_node_ids:
        lines.append(f"  - {_predicted_line(requirement_id, report)}")
    return lines


def _render_verdict_group_list(
    groups: list[MatchGroup],
    report: EvaluationReport,
) -> list[str]:
    if not groups:
        return ["- none"]
    lines = []
    for index, group in enumerate(groups, start=1):
        rendered = _render_verdict_group(group, report)
        if len(rendered) == 1:
            lines.append(rendered[0])
        else:
            lines.append(f"- group {index}:")
            lines.extend(rendered)
    return lines


def _render_verdict_header_line(
    topic_id: str,
    requirement_id: str,
    report: EvaluationReport,
) -> str:
    acceptable = report.acceptable_verdicts_by_topic.get(topic_id)
    verdict = report.predicted_verdict_labels.get(requirement_id)
    verdict_display = verdict if verdict else "not verifiable by text"
    citation_suffix = _citation_status_suffix(requirement_id, report)
    return (
        f"- `{topic_id}` — acceptable: {acceptable}, "
        f"predicted: {verdict_display}{citation_suffix}"
    )


def _render_model_detail_lines(
    requirement_id: str,
    report: EvaluationReport,
) -> list[str]:
    text = _collapse_whitespace(
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
            f'"{_collapse_whitespace(chunk_text)}"'
        )
    if not evidence_quotes:
        lines.append("  - **model's evidence (what it chose to cite):** none")
    for quote in evidence_quotes:
        lines.append(
            f"  - **model's evidence (what it chose to cite):** "
            f'"{_collapse_whitespace(quote)}"'
        )
    if reasoning:
        lines.append(
            f"  - **model's reasoning:** {_collapse_whitespace(reasoning)}"
        )
    return lines


def _render_expected_detail_lines(
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
            f'"{_collapse_whitespace(quote)}"'
        )
    if rationale:
        lines.append(
            f"  - **expected reasoning:** {_collapse_whitespace(rationale)}"
        )
    return lines


def _render_verdict_group_with_detail(
    group: MatchGroup,
    report: EvaluationReport,
) -> list[str]:
    if len(group.true_topic_ids) == 1 and len(group.predicted_node_ids) == 1:
        topic_id = group.true_topic_ids[0]
        requirement_id = group.predicted_node_ids[0]
        lines = [_render_verdict_header_line(topic_id, requirement_id, report)]
        lines.extend(_render_model_detail_lines(requirement_id, report))
        lines.extend(_render_expected_detail_lines(topic_id, report))
        return lines
    lines = []
    for topic_id in group.true_topic_ids:
        acceptable = report.acceptable_verdicts_by_topic.get(topic_id)
        lines.append(
            f"- {_true_line(topic_id, report)} (acceptable: {acceptable})"
        )
        lines.extend(
            f"  {line}" for line in _render_expected_detail_lines(
                topic_id, report
            )
        )
    for requirement_id in group.predicted_node_ids:
        lines.append(f"  - {_predicted_line(requirement_id, report)}")
        lines.extend(
            f"  {line}" for line in _render_model_detail_lines(
                requirement_id, report
            )
        )
    return lines


def _render_verdict_group_list_with_detail(
    groups: list[MatchGroup],
    report: EvaluationReport,
) -> list[str]:
    if not groups:
        return ["- none"]
    lines = []
    for group in groups:
        lines.extend(_render_verdict_group_with_detail(group, report))
        lines.append("")
    return lines[:-1]


def _render_verdict_section(report: EvaluationReport) -> list[str]:
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
    counts = _confusion_counts(report)
    lines.extend(_render_confusion_table(counts))
    lines.extend(_render_confusion_gaps(counts, report))
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
        _render_verdict_group_list_with_detail(
            result.mismatched_clean_groups, report
        )
    )
    lines.append("")
    lines.append(
        "**False-compliant rate** — dangerous direction: the true verdict "
        "requires an issue (anything but `compliant`), but every predicted "
        "verdict in the group is `compliant`."
    )
    lines.append(f"- rate: {_percent(result.false_compliant_rate)}")
    lines.append("")
    lines.extend(
        _render_verdict_group_list_with_detail(
            result.false_compliant_groups, report
        )
    )
    lines.append("")
    lines.append(
        "**False-issue rate** — mirror direction: the true verdict is "
        "`compliant` only, but the pipeline raised an issue anyway."
    )
    lines.append(f"- rate: {_percent(result.false_issue_rate)}")
    lines.append("")
    lines.extend(
        _render_verdict_group_list_with_detail(
            result.false_issue_groups, report
        )
    )
    lines.append("")
    lines.append(
        "**Unscored** — split/merge groups excluded from the matrix above "
        "(still counted in the two rates above):"
    )
    lines.extend(_render_verdict_group_list(result.unscored_groups, report))
    lines.append("")
    return lines


def _render_evidence_section(report: EvaluationReport) -> list[str]:
    citation_result = report.evidence_citation_verified
    recall_result = report.evidence_recall
    lines = ["## Evidence", ""]
    lines.append(
        "**Citation-verified rate** (evidence-level): fraction of evidence "
        "quotes actually located in application.txt."
    )
    lines.append(
        f"- rate: {_percent(citation_result.citation_verified_rate)} "
        f"({citation_result.unverified_evidence_count} unverified of "
        f"{citation_result.total_evidence_count})"
    )
    lines.append("")
    lines.append(
        "**Evidence recall**: does the expected evidence span (from "
        "`true_verdicts.json`) show up somewhere in the requirement's "
        "retrieved chunks, before the verdict step chose what to cite? "
        "Topics never extracted as a requirement are excluded — that "
        "failure is already counted by requirement recall above."
    )
    lines.append(
        f"- recall: {_percent(recall_result.recall)} "
        f"({recall_result.matched_topic_count}/"
        f"{recall_result.total_topic_count})"
    )
    lines.append("- missed:")
    if not recall_result.missed_topic_ids:
        lines.append("  - none")
    for topic_id in recall_result.missed_topic_ids:
        lines.append(f"  - {_true_line(topic_id, report)}")
        evidence_quotes = report.true_evidence_by_topic.get(topic_id, [])
        for quote in evidence_quotes:
            lines.append(
                f'    expected evidence: "{_collapse_whitespace(quote)}"'
            )
    lines.append("")
    return lines


def _verdict_accuracy_ratio(result: VerdictAccuracyResult) -> float | None:
    if result.clean_match_count <= 0:
        return None
    correct = result.clean_match_count - len(result.mismatched_clean_groups)
    return correct / result.clean_match_count


def _round_or_none(value: float | None) -> float | None:
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
        "verdict_accuracy": _round_or_none(
            _verdict_accuracy_ratio(report.verdict_accuracy)
        ),
        "false_compliant_rate": round(
            report.verdict_accuracy.false_compliant_rate, 4
        ),
        "false_issue_rate": round(
            report.verdict_accuracy.false_issue_rate, 4
        ),
        "evidence_citation_verified_rate": round(
            report.evidence_citation_verified.citation_verified_rate, 4
        ),
        "evidence_recall": round(report.evidence_recall.recall, 4),
        "verdict_only_accuracy": _round_or_none(verdict_only_accuracy),
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


def render_report_as_markdown(
    report: EvaluationReport,
    verdict_only_accuracy: float | None = None,
    verdict_only_scored: int | None = None,
) -> str:
    sections = ["# Evaluation report", ""]
    sections.extend(render_metrics_summary_lines(
        report, verdict_only_accuracy, verdict_only_scored,
    ))
    sections.extend(_render_recall_section(report))
    sections.extend(_render_precision_section(report))
    sections.extend(_render_coverage_section(report))
    sections.extend(_render_is_mandatory_section(report))
    sections.extend(_render_is_text_verifiable_section(report))
    sections.extend(_render_verdict_section(report))
    sections.extend(_render_evidence_section(report))
    return "\n".join(sections)
