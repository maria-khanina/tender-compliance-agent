"""Renders an EvaluationReport as a human-readable markdown report."""
from evaluation.orchestrator import EvaluationReport
from evaluation.rendering._coverage_section import render_coverage_section
from evaluation.rendering._evidence_section import render_evidence_section
from evaluation.rendering._flag_accuracy_sections import (
    render_is_mandatory_section,
    render_is_text_verifiable_section,
)
from evaluation.rendering._matching_sections import (
    render_precision_section,
    render_recall_section,
)
from evaluation.rendering._summary import (
    build_summary_metrics,
    render_metrics_summary_lines,
)
from evaluation.rendering._verdict_section import render_verdict_section

__all__ = ["build_summary_metrics", "render_report_as_markdown"]


def render_report_as_markdown(
    report: EvaluationReport,
    verdict_only_accuracy: float | None = None,
    verdict_only_scored: int | None = None,
    missed_chunk_diagnostics: dict[str, str] | None = None,
    unexplained_diagnostics: dict[str, str] | None = None,
) -> str:
    sections = ["# Evaluation report", ""]
    sections.extend(render_metrics_summary_lines(
        report, verdict_only_accuracy, verdict_only_scored,
    ))
    sections.extend(render_recall_section(report, missed_chunk_diagnostics))
    sections.extend(render_precision_section(report, unexplained_diagnostics))
    sections.extend(render_coverage_section(report))
    sections.extend(render_is_mandatory_section(report))
    sections.extend(render_is_text_verifiable_section(report))
    sections.extend(render_verdict_section(report))
    sections.extend(render_evidence_section(report))
    return "\n".join(sections)
