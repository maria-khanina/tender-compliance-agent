from evaluation.metrics import (
    CoverageFlag,
    IsMandatoryResult,
    PrecisionResult,
    RecallResult,
    VerdictAccuracyResult,
)
from evaluation.orchestrator import EvaluationReport


PERCENT_SCALE = 100.0


def _percent(ratio: float) -> str:
    return f"{ratio * PERCENT_SCALE:.1f}%"


def _list_or_none(items: list[str]) -> str:
    if not items:
        return "none"
    return ", ".join(items)


def _render_recall_section(result: RecallResult) -> list[str]:
    lines = ["## Requirement recall", ""]
    lines.append(
        f"- recall: {_percent(result.recall)} "
        f"({result.matched_topic_count}/{result.total_topic_count})"
    )
    lines.append(f"- missed: {_list_or_none(result.missed_topic_ids)}")
    lines.append(
        f"- over-split: {_list_or_none(result.over_split_topic_ids)}"
    )
    lines.append(
        f"- over-merge: {_list_or_none(result.over_merge_topic_ids)}"
    )
    lines.append(f"- tangled: {_list_or_none(result.tangled_topic_ids)}")
    lines.append("")
    return lines


def _render_precision_section(result: PrecisionResult) -> list[str]:
    lines = ["## Requirement precision", ""]
    lines.append(
        "- citation-verified rate (hallucination proxy): "
        f"{_percent(result.citation_verified_rate)}"
    )
    lines.append(
        f"- unverified: {_list_or_none(result.unverified_requirement_ids)}"
    )
    lines.append(
        "- classification precision: "
        f"{_percent(result.classification_precision)}"
    )
    lines.append(
        "- unexplained (fixture gap candidates, needs manual triage): "
        f"{_list_or_none(result.unexplained_requirement_ids)}"
    )
    lines.append("")
    return lines


def _render_coverage_flag(flag: CoverageFlag) -> str:
    expected_part = "+".join(flag.expected_topic_ids)
    actual_part = "+".join(flag.actual_node_ids)
    return (
        f"- {expected_part} -> {actual_part}: "
        f"expected_covered={_percent(flag.expected_covered_ratio)}, "
        f"actual_explained={_percent(flag.actual_explained_ratio)}"
    )


def _render_coverage_section(flags: list[CoverageFlag]) -> list[str]:
    lines = ["## Coverage flags", ""]
    if not flags:
        lines.append("none")
    else:
        lines.extend(_render_coverage_flag(flag) for flag in flags)
    lines.append("")
    return lines


def _render_is_mandatory_section(result: IsMandatoryResult) -> list[str]:
    lines = ["## is_mandatory accuracy", ""]
    lines.append(
        f"- accuracy: {_percent(result.accuracy)} "
        f"({result.scored_topic_count} scored)"
    )
    lines.append(
        f"- mismatched: {_list_or_none(result.mismatched_topic_ids)}"
    )
    lines.append("")
    return lines


def _render_confusion_matrix(result: VerdictAccuracyResult) -> list[str]:
    if not result.confusion_matrix:
        return ["- confusion matrix: none"]
    lines = []
    for cell in result.confusion_matrix:
        lines.append(
            f"- {cell.expected_verdict} -> {cell.actual_verdict}: "
            f"{cell.count}"
        )
    return lines


def _render_verdict_section(result: VerdictAccuracyResult) -> list[str]:
    lines = ["## Verdict accuracy", ""]
    lines.append(f"- clean matches scored: {result.clean_match_count}")
    lines.extend(_render_confusion_matrix(result))
    lines.append(
        "- false-compliant rate (dangerous direction): "
        f"{_percent(result.false_compliant_rate)}"
    )
    lines.append(
        f"  groups: {_list_or_none(result.false_compliant_group_ids)}"
    )
    lines.append(
        f"- false-issue rate: {_percent(result.false_issue_rate)}"
    )
    lines.append(
        f"  groups: {_list_or_none(result.false_issue_group_ids)}"
    )
    lines.append(
        f"- unscored (split/merge groups): "
        f"{_list_or_none(result.unscored_group_ids)}"
    )
    lines.append(
        "- not verifiable (matched actual has no verdict at all, "
        "likely is_text_verifiable=False): "
        f"{_list_or_none(result.not_verifiable_group_ids)}"
    )
    lines.append("")
    return lines


def _render_evidence_section(report: EvaluationReport) -> list[str]:
    citation_result = report.evidence_citation_verified
    recall_result = report.evidence_recall
    lines = ["## Evidence", ""]
    lines.append(
        "- citation-verified rate (evidence-level): "
        f"{_percent(citation_result.citation_verified_rate)} "
        f"({citation_result.unverified_evidence_count} unverified of "
        f"{citation_result.total_evidence_count})"
    )
    lines.append(
        "- evidence recall (retrieved set vs. expected evidence): "
        f"{_percent(recall_result.recall)} "
        f"({recall_result.matched_topic_count}/"
        f"{recall_result.total_topic_count})"
    )
    lines.append(f"  missed: {_list_or_none(recall_result.missed_topic_ids)}")
    lines.append("")
    return lines


def render_report_as_markdown(report: EvaluationReport) -> str:
    sections = ["# Evaluation report", ""]
    sections.extend(_render_recall_section(report.requirement_recall))
    sections.extend(_render_precision_section(report.requirement_precision))
    sections.extend(_render_coverage_section(report.coverage_flags))
    sections.extend(
        _render_is_mandatory_section(report.is_mandatory_accuracy)
    )
    sections.extend(_render_verdict_section(report.verdict_accuracy))
    sections.extend(_render_evidence_section(report))
    return "\n".join(sections)
