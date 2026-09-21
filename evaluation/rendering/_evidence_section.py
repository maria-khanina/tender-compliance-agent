"""Evidence citation-verification and recall report section."""
from evaluation.orchestrator import EvaluationReport
from evaluation.rendering._common import collapse_whitespace, percent, true_line


def render_evidence_section(report: EvaluationReport) -> list[str]:
    citation_result = report.evidence_citation_verified
    recall_result = report.evidence_recall
    lines = ["## Evidence", ""]
    lines.append(
        "**Citation-verified rate** (evidence-level): fraction of evidence "
        "quotes actually located in application.txt."
    )
    lines.append(
        f"- rate: {percent(citation_result.citation_verified_rate)} "
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
