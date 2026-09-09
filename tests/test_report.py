from schemas import (
    Chunk,
    DocumentSource,
    Evidence,
    EvidenceRole,
    Requirement,
    RetrievedEvidenceRecord,
    TextSpan,
    Verdict,
    VerdictLabel,
)
from steps.report import build_report


def _build_requirement(
    requirement_id: str,
    text: str,
    is_mandatory: bool = True,
    is_text_verifiable: bool = True,
) -> Requirement:
    citation = TextSpan(
        document_path="tender.txt",
        quote=text,
        start_char=0,
        end_char=len(text),
        citation_verified=True,
    )
    return Requirement(
        requirement_id=requirement_id,
        text=text,
        is_mandatory=is_mandatory,
        is_text_verifiable=is_text_verifiable,
        citations=[citation],
        conditions=[],
    )


def _build_verdict(
    requirement_id: str,
    verdict_label: VerdictLabel,
    citation_verified: bool = True,
) -> Verdict:
    evidence = Evidence(
        document_path="application.txt",
        quote="supporting quote",
        start_char=0,
        end_char=10,
        citation_verified=citation_verified,
        role=EvidenceRole.SUPPORTS,
    )
    return Verdict(
        requirement_id=requirement_id,
        verdict=verdict_label,
        evidence=[evidence],
        reasoning="because",
    )


def test_mandatory_and_preferred_requirements_are_separated() -> None:
    mandatory_requirement = _build_requirement(
        "req-1", "Mandatory requirement text", is_mandatory=True
    )
    preferred_requirement = _build_requirement(
        "req-2", "Preferred requirement text", is_mandatory=False
    )
    verdicts = [
        _build_verdict("req-1", VerdictLabel.COMPLIANT),
        _build_verdict("req-2", VerdictLabel.COMPLIANT),
    ]
    report = build_report(
        [mandatory_requirement, preferred_requirement], verdicts, []
    )
    mandatory_header_index = report.index("## Mandatory Requirements")
    preferred_header_index = report.index(
        "## Preferred (Non-mandatory) Requirements"
    )
    mandatory_text_index = report.index("Mandatory requirement text")
    preferred_text_index = report.index("Preferred requirement text")
    assert mandatory_header_index < mandatory_text_index
    assert preferred_header_index < preferred_text_index
    assert mandatory_header_index < preferred_header_index


def test_verdicts_sorted_by_severity_within_section() -> None:
    requirements = [
        _build_requirement("req-compliant", "Compliant requirement"),
        _build_requirement("req-non-compliant", "Non-compliant requirement"),
        _build_requirement("req-contradictory", "Contradictory requirement"),
        _build_requirement("req-insufficient", "Insufficient requirement"),
    ]
    verdicts = [
        _build_verdict("req-compliant", VerdictLabel.COMPLIANT),
        _build_verdict("req-non-compliant", VerdictLabel.NON_COMPLIANT),
        _build_verdict("req-contradictory", VerdictLabel.CONTRADICTORY),
        _build_verdict(
            "req-insufficient", VerdictLabel.INSUFFICIENT_INFORMATION
        ),
    ]
    report = build_report(requirements, verdicts, [])
    non_compliant_index = report.index("Non-compliant requirement")
    contradictory_index = report.index("Contradictory requirement")
    insufficient_index = report.index("Insufficient requirement")
    compliant_index = report.index("Compliant requirement")
    assert non_compliant_index < contradictory_index
    assert contradictory_index < insufficient_index
    assert insufficient_index < compliant_index


def test_not_text_verifiable_requirement_gets_own_section() -> None:
    verifiable_requirement = _build_requirement(
        "req-1", "Verifiable requirement", is_text_verifiable=True
    )
    not_verifiable_requirement = _build_requirement(
        "req-2", "Not verifiable requirement", is_text_verifiable=False
    )
    verdicts = [_build_verdict("req-1", VerdictLabel.COMPLIANT)]
    evidence_chunk = Chunk(
        document_source=DocumentSource.APPLICATION,
        document_path="application.txt",
        chunk_index=0,
        text="Possibly relevant application text",
        start_char=0,
        end_char=10,
    )
    retrieved_evidence = [
        RetrievedEvidenceRecord(
            requirement_id="req-2", evidence_chunks=[evidence_chunk]
        )
    ]
    report = build_report(
        [verifiable_requirement, not_verifiable_requirement],
        verdicts,
        retrieved_evidence,
    )
    section_index = report.index(
        "## Not Verifiable From Application Text Alone"
    )
    requirement_index = report.index("Not verifiable requirement")
    evidence_index = report.index("Possibly relevant application text")
    assert section_index < requirement_index < evidence_index
    assert "## Mandatory Requirements" in report
    mandatory_section = report[:section_index]
    assert "Not verifiable requirement" not in mandatory_section


def test_unverified_citation_is_flagged_and_listed() -> None:
    requirement = _build_requirement("req-1", "Requirement with bad quote")
    verdict = _build_verdict(
        "req-1", VerdictLabel.COMPLIANT, citation_verified=False
    )
    report = build_report([requirement], [verdict], [])
    assert "(quote not located verbatim in source text)" in report
    review_section_index = report.index(
        "## Needs Manual Review: Unverified Citations"
    )
    review_mention_index = report.index(
        "Requirement with bad quote", review_section_index
    )
    assert review_mention_index > review_section_index
