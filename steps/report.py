from logging_config import get_logger
from schemas import (
    Chunk,
    Requirement,
    RetrievedEvidenceRecord,
    Verdict,
    VerdictLabel,
)


VERDICT_LABEL_DISPLAY_TEXT: dict[VerdictLabel, str] = {
    VerdictLabel.COMPLIANT: "Compliant",
    VerdictLabel.NON_COMPLIANT: "Non-compliant",
    VerdictLabel.INSUFFICIENT_INFORMATION: "Insufficient information",
    VerdictLabel.CONTRADICTORY: "Contradictory",
}

VERDICT_SEVERITY_ORDER: list[VerdictLabel] = [
    VerdictLabel.NON_COMPLIANT,
    VerdictLabel.CONTRADICTORY,
    VerdictLabel.INSUFFICIENT_INFORMATION,
    VerdictLabel.COMPLIANT,
]

logger = get_logger(__name__)


class RequirementVerdictPair:
    def __init__(self, requirement: Requirement, verdict: Verdict) -> None:
        self.requirement = requirement
        self.verdict = verdict


def _build_requirement_lookup(
    requirements: list[Requirement],
) -> dict[str, Requirement]:
    lookup = {}
    for requirement in requirements:
        lookup[requirement.requirement_id] = requirement
    return lookup


def _build_retrieved_evidence_lookup(
    retrieved_evidence: list[RetrievedEvidenceRecord],
) -> dict[str, list[Chunk]]:
    lookup = {}
    for record in retrieved_evidence:
        lookup[record.requirement_id] = record.evidence_chunks
    return lookup


def _build_verdict_pairs(
    requirements: list[Requirement],
    verdicts: list[Verdict],
) -> list[RequirementVerdictPair]:
    requirement_lookup = _build_requirement_lookup(requirements)
    pairs = []
    for verdict in verdicts:
        requirement = requirement_lookup[verdict.requirement_id]
        pairs.append(RequirementVerdictPair(requirement, verdict))
    return pairs


def _split_by_mandatory(
    pairs: list[RequirementVerdictPair],
) -> tuple[list[RequirementVerdictPair], list[RequirementVerdictPair]]:
    mandatory_pairs = []
    preferred_pairs = []
    for pair in pairs:
        if pair.requirement.is_mandatory:
            mandatory_pairs.append(pair)
        else:
            preferred_pairs.append(pair)
    return mandatory_pairs, preferred_pairs


def _severity_rank(pair: RequirementVerdictPair) -> int:
    return VERDICT_SEVERITY_ORDER.index(pair.verdict.verdict)


def _sort_by_severity(
    pairs: list[RequirementVerdictPair],
) -> list[RequirementVerdictPair]:
    return sorted(pairs, key=_severity_rank)


def _format_evidence_lines(verdict: Verdict) -> list[str]:
    if not verdict.evidence:
        return []
    evidence_entries = []
    for evidence in verdict.evidence:
        entry = f"- ({evidence.role.value}) {evidence.quote}"
        if not evidence.citation_verified:
            entry += " *(quote not located verbatim in source text)*"
        evidence_entries.append(entry)
    return ["**Evidence:**"] + evidence_entries


def _format_verdict_section(pair: RequirementVerdictPair) -> str:
    display_label = VERDICT_LABEL_DISPLAY_TEXT[pair.verdict.verdict]
    section_lines = []
    section_lines.append(f"### {display_label}")
    section_lines.append("")
    section_lines.append(f"**Requirement:** {pair.requirement.text}")
    section_lines.append("")
    section_lines.append(f"**Reasoning:** {pair.verdict.reasoning}")
    section_lines.append("")
    section_lines.extend(_format_evidence_lines(pair.verdict))
    return "\n".join(section_lines)


def _render_requirement_group(
    title: str,
    pairs: list[RequirementVerdictPair],
) -> list[str]:
    if not pairs:
        return []
    section_lines = [f"## {title}", ""]
    sorted_pairs = _sort_by_severity(pairs)
    for pair in sorted_pairs:
        section_lines.append(_format_verdict_section(pair))
        section_lines.append("")
    return section_lines


def _not_text_verifiable_requirements(
    requirements: list[Requirement],
) -> list[Requirement]:
    not_verifiable = []
    for requirement in requirements:
        if not requirement.is_text_verifiable:
            not_verifiable.append(requirement)
    return not_verifiable


def _format_not_verifiable_entry(
    requirement: Requirement,
    evidence_chunks: list[Chunk],
) -> str:
    entry_lines = []
    entry_lines.append(f"### {requirement.text}")
    entry_lines.append("")
    entry_lines.append(
        "This cannot be confirmed from the application text alone and "
        "requires independent verification."
    )
    if evidence_chunks:
        entry_lines.append("")
        entry_lines.append(
            "**Possibly relevant excerpts from the application:**"
        )
        for chunk in evidence_chunks:
            entry_lines.append(f"- {chunk.text}")
    return "\n".join(entry_lines)


def _render_not_verifiable_section(
    requirements: list[Requirement],
    retrieved_evidence_lookup: dict[str, list[Chunk]],
) -> list[str]:
    not_verifiable = _not_text_verifiable_requirements(requirements)
    if not not_verifiable:
        return []
    section_lines = [
        "## Not Verifiable From Application Text Alone", "",
    ]
    for requirement in not_verifiable:
        evidence_chunks = retrieved_evidence_lookup.get(
            requirement.requirement_id, []
        )
        section_lines.append(
            _format_not_verifiable_entry(requirement, evidence_chunks)
        )
        section_lines.append("")
    return section_lines


def _unverified_citation_note(pair: RequirementVerdictPair) -> str | None:
    unverified_quotes = []
    for evidence in pair.verdict.evidence:
        if not evidence.citation_verified:
            unverified_quotes.append(evidence.quote)
    if not unverified_quotes:
        return None
    quotes_text = "; ".join(f'"{quote}"' for quote in unverified_quotes)
    return f"- **{pair.requirement.text}** — {quotes_text}"


def _render_unverified_citations_section(
    pairs: list[RequirementVerdictPair],
) -> list[str]:
    notes = []
    for pair in pairs:
        note = _unverified_citation_note(pair)
        if note is not None:
            notes.append(note)
    if not notes:
        return []
    section_lines = [
        "## Needs Manual Review: Unverified Citations", "",
        "The following verdicts cite quotes that could not be located "
        "verbatim in the application text:", "",
    ]
    section_lines.extend(notes)
    section_lines.append("")
    return section_lines


def build_report(
    requirements: list[Requirement],
    verdicts: list[Verdict],
    retrieved_evidence: list[RetrievedEvidenceRecord],
) -> str:
    pairs = _build_verdict_pairs(requirements, verdicts)
    mandatory_pairs, preferred_pairs = _split_by_mandatory(pairs)
    retrieved_evidence_lookup = _build_retrieved_evidence_lookup(
        retrieved_evidence
    )
    report_sections = ["# Tender Compliance Report", ""]
    report_sections.extend(
        _render_requirement_group("Mandatory Requirements", mandatory_pairs)
    )
    report_sections.extend(
        _render_requirement_group(
            "Preferred (Non-mandatory) Requirements", preferred_pairs
        )
    )
    report_sections.extend(
        _render_not_verifiable_section(requirements, retrieved_evidence_lookup)
    )
    report_sections.extend(_render_unverified_citations_section(pairs))
    report_text = "\n".join(report_sections)
    logger.info(
        "Built report covering %d requirement(s) and %d verdict(s)",
        len(requirements),
        len(verdicts),
    )
    return report_text
