from evaluation.fixtures import (
    SourceSpan,
    TrueRequirement,
    TrueRequirementsFixture,
    TrueSource,
    TrueVerdict,
    TrueVerdictsFixture,
)
from evaluation.verdict_only import (
    build_synthetic_requirements,
    score_verdicts,
)
from schemas import Verdict, VerdictLabel


def _true_requirement(topic_id: str) -> TrueRequirement:
    return TrueRequirement(
        topic_id=topic_id,
        description=f"Description for {topic_id}",
        is_mandatory=True,
        is_text_verifiable=True,
        source=TrueSource(
            document_path="tender.txt",
            quote="some quote",
            spans=[SourceSpan(start_char=0, end_char=10)],
        ),
    )


def _verdict(topic_id: str, label: VerdictLabel) -> Verdict:
    return Verdict(
        requirement_id=topic_id,
        requirement_text=f"Description for {topic_id}",
        verdict=label,
        evidence=[],
        reasoning="",
        condition_holds=True,
    )


def test_build_synthetic_requirements_uses_topic_id_and_true_flags() -> None:
    fixture = TrueRequirementsFixture(
        notes=[],
        requirements=[_true_requirement("topic_a")],
    )
    requirements = build_synthetic_requirements(fixture)
    assert len(requirements) == 1
    requirement = requirements[0]
    assert requirement.requirement_id == "topic_a"
    assert requirement.is_text_verifiable is True
    assert requirement.citations[0].quote == "some quote"


def _true_verdict(
    topic_id: str,
    acceptable_verdicts: list[str] | None,
) -> TrueVerdict:
    return TrueVerdict(
        topic_id=topic_id,
        acceptable_verdicts=acceptable_verdicts,
        rationale="",
        evidence=[],
    )


def test_score_verdicts_matches_by_topic_id() -> None:
    verdicts_fixture = TrueVerdictsFixture(
        notes=[],
        verdicts=[
            _true_verdict("topic_a", ["compliant"]),
            _true_verdict("topic_b", ["non_compliant", "insufficient_information"]),
        ],
    )
    predicted = [
        _verdict("topic_a", VerdictLabel.COMPLIANT),
        _verdict("topic_b", VerdictLabel.COMPLIANT),
    ]
    result = score_verdicts(predicted, verdicts_fixture)
    assert result.scored_topic_count == 2
    assert result.accuracy == 1 / 2
    assert len(result.mismatches) == 1
    assert result.mismatches[0].topic_id == "topic_b"


def test_score_verdicts_skips_topics_with_no_acceptable_verdicts() -> None:
    verdicts_fixture = TrueVerdictsFixture(
        notes=[],
        verdicts=[_true_verdict("topic_a", None)],
    )
    predicted = [_verdict("topic_a", VerdictLabel.COMPLIANT)]
    result = score_verdicts(predicted, verdicts_fixture)
    assert result.scored_topic_count == 0
    assert result.accuracy == 0.0
