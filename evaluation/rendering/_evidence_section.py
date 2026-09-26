"""Evidence hallucination-rate and context-recall report section."""
from evaluation.orchestrator import EvaluationReport
from evaluation.rendering._common import collapse_whitespace, percent, true_line


def render_evidence_section(report: EvaluationReport) -> list[str]:
    hallucination_result = report.evidence_hallucination
    recall_result = report.context_recall
    lines = ["## Evidence", ""]
    lines.append(
        "**Evidence hallucination rate**: fraction of the model's cited "
        "evidence quotes that were NOT actually located in application.txt "
        "(the model asserted a quote that isn't really there)."
    )
    lines.append(
        f"- rate: {percent(hallucination_result.hallucination_rate)} "
        f"({hallucination_result.hallucinated_evidence_count} hallucinated "
        f"of {hallucination_result.total_evidence_count})"
    )
    lines.append("")
    lines.append(
        "**Context recall**: does the expected evidence span (from "
        "`true_verdicts.json`) show up somewhere in the requirement's "
        "retrieved chunks, before the verdict step chose what to cite? "
        "Topics never extracted as a requirement are excluded — that "
        "failure is already counted by requirement recall above."
    )
    lines.append(
        f"- recall: {percent(recall_result.recall)} "
        f"({recall_result.matched_topic_count}/"
        f"{recall_result.total_topic_count})"
    )
    lines.append("- missed:")
    if not recall_result.missed_topic_ids:
        lines.append("  - none")
    for topic_id in recall_result.missed_topic_ids:
        lines.append(f"  - {true_line(topic_id, report)}")
        evidence_quotes = report.true_evidence_by_topic.get(topic_id, [])
        for quote in evidence_quotes:
            lines.append(
                f'    expected evidence: "{collapse_whitespace(quote)}"'
            )
    lines.append("")
    return lines
