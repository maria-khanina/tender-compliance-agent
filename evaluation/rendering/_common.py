"""Shared string-rendering helpers used across every report section."""
from evaluation.orchestrator import EvaluationReport

PERCENT_SCALE = 100.0
SHORT_ID_LENGTH = 8
RETRIEVED_CONTEXT_MAX_CHARS = 280


def percent(ratio: float) -> str:
    return f"{ratio * PERCENT_SCALE:.1f}%"


def collapse_whitespace(text: str) -> str:
    return " ".join(text.split())


def truncate(text: str, max_chars: int = RETRIEVED_CONTEXT_MAX_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + " [...truncated]"


def true_line(topic_id: str, report: EvaluationReport) -> str:
    quote = report.true_quotes_by_topic.get(topic_id, "(quote unavailable)")
    return f'true `{topic_id}` — "{collapse_whitespace(quote)}"'


def citation_status_suffix(requirement_id: str, report: EvaluationReport) -> str:
    status = report.predicted_citation_status.get(requirement_id, "precise")
    if status == "unverified":
        return ", citation: UNVERIFIED — not located in tender.txt"
    if status == "fuzzy":
        return ", citation: fuzzy match — worth a second look"
    return ""


def predicted_text_line(requirement_id: str, report: EvaluationReport) -> str:
    text = report.predicted_texts.get(requirement_id, "(text unavailable)")
    short_id = requirement_id[:SHORT_ID_LENGTH]
    return f'predicted [{short_id}] "{collapse_whitespace(text)}"'


def predicted_line(requirement_id: str, report: EvaluationReport) -> str:
    verdict = report.predicted_verdict_labels.get(requirement_id)
    if verdict:
        verdict_suffix = f" — verdict: {verdict}"
    else:
        verdict_suffix = " — not verifiable by text"
    citation_suffix = citation_status_suffix(requirement_id, report)
    return (
        f"{predicted_text_line(requirement_id, report)}"
        f"{verdict_suffix}{citation_suffix}"
    )
