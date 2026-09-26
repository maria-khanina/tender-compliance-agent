from schemas import (
    Evidence,
    EvidenceRole,
    MatchPrecision,
    Requirement,
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
    citation_verified: bool = True,
) -> Requirement:
    citation = TextSpan(
        document_path="tender.txt",
        quote=text,
        start_char=0,
        end_char=len(text),
        citation_verified=citation_verified,
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
    requirement_text: str,
    verdict_label: VerdictLabel,
    citation_verified: bool = True,
    match_precision: MatchPrecision | None = "precise",
) -> Verdict:
    evidence = Evidence(
        document_path="application.txt",
        quote="supporting quote",
        start_char=0,
        end_char=10,
        citation_verified=citation_verified,
        match_precision=match_precision,
        role=EvidenceRole.SUPPORTS,
    )
    return Verdict(
        requirement_id=requirement_id,
        requirement_text=requirement_text,
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
        _build_verdict(
            "req-1", "Mandatory requirement text", VerdictLabel.COMPLIANT
        ),
        _build_verdict(
            "req-2", "Preferred requirement text", VerdictLabel.COMPLIANT
        ),
    ]
    report = build_report(
        [mandatory_requirement, preferred_requirement], verdicts
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
    assert "**REQUIREMENT:** Mandatory requirement text" in report
    assert "**PREFERENCE:** Preferred requirement text" in report


def test_verdicts_sorted_by_severity_within_section() -> None:
    requirements = [
        _build_requirement("req-compliant", "Compliant requirement"),
        _build_requirement("req-non-compliant", "Non-compliant requirement"),
        _build_requirement("req-contradictory", "Contradictory requirement"),
        _build_requirement("req-insufficient", "Insufficient requirement"),
    ]
    verdicts = [
        _build_verdict(
            "req-compliant", "Compliant requirement", VerdictLabel.COMPLIANT
        ),
        _build_verdict(
            "req-non-compliant", "Non-compliant requirement",
            VerdictLabel.NON_COMPLIANT,
        ),
        _build_verdict(
            "req-contradictory", "Contradictory requirement",
            VerdictLabel.CONTRADICTORY,
        ),
        _build_verdict(
            "req-insufficient", "Insufficient requirement",
            VerdictLabel.INSUFFICIENT_INFORMATION,
        ),
    ]
    report = build_report(requirements, verdicts)
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
    verdicts = [
        _build_verdict(
            "req-1", "Verifiable requirement", VerdictLabel.COMPLIANT
        )
    ]
    report = build_report(
        [verifiable_requirement, not_verifiable_requirement], verdicts
    )
    section_index = report.index(
        "## Not Verifiable From Application Text Alone"
    )
    requirement_index = report.index("Not verifiable requirement")
    assert section_index < requirement_index
    assert "## Mandatory Requirements" in report
    mandatory_section = report[:section_index]
    assert "Not verifiable requirement" not in mandatory_section


def test_fuzzy_evidence_match_is_flagged_inline() -> None:
    requirement = _build_requirement("req-1", "Requirement text")
    verdict = _build_verdict(
        "req-1", "Requirement text", VerdictLabel.COMPLIANT,
        match_precision="fuzzy",
    )
    report = build_report([requirement], [verdict])
    assert "worth a second look" in report


def test_unverified_evidence_citation_is_flagged_and_listed() -> None:
    requirement = _build_requirement("req-1", "Requirement with bad quote")
    verdict = _build_verdict(
        "req-1", "Requirement with bad quote", VerdictLabel.COMPLIANT,
        citation_verified=False,
    )
    report = build_report([requirement], [verdict])
    assert "[UNVERIFIED:" in report
    review_section_index = report.index(
        "## Needs Manual Review: Unverified Citations"
    )
    evidence_subsection_index = report.index(
        "### Evidence quotes not found in the application text",
        review_section_index,
    )
    review_mention_index = report.index(
        "Requirement with bad quote", evidence_subsection_index
    )
    assert review_mention_index > evidence_subsection_index


def test_unverified_requirement_citation_is_flagged_and_listed() -> None:
    requirement = _build_requirement(
        "req-1", "Requirement never located in tender", citation_verified=False
    )
    verdict = _build_verdict(
        "req-1", "Requirement never located in tender", VerdictLabel.COMPLIANT
    )
    report = build_report([requirement], [verdict])
    review_section_index = report.index(
        "## Needs Manual Review: Unverified Citations"
    )
    requirement_subsection_index = report.index(
        "### Requirement quotes not found in the tender text",
        review_section_index,
    )
    review_mention_index = report.index(
        "Requirement never located in tender", requirement_subsection_index
    )
    assert review_mention_index > requirement_subsection_index
