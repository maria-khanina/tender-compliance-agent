from pydantic import BaseModel

from evaluation.fixtures import (
    TrueRequirement,
    TrueRequirementsFixture,
    TrueVerdictsFixture,
)
from evaluation.span_adapters import retrieved_by_requirement
from schemas import (
    ConditionSpec,
    Requirement,
    RetrievedEvidenceRecord,
    TextSpan,
    Verdict,
)


def _synthetic_requirement(true_requirement: TrueRequirement) -> Requirement:
    source = true_requirement.source
    citations = []
    for span in source.spans:
        citations.append(TextSpan(
            document_path=source.document_path,
            quote=source.quote,
            start_char=span.start_char,
            end_char=span.end_char,
            citation_verified=True,
            match_precision="precise",
        ))
    conditions: list[ConditionSpec] = []
    return Requirement(
        requirement_id=true_requirement.topic_id,
        text=true_requirement.description,
        is_mandatory=true_requirement.is_mandatory,
        is_text_verifiable=true_requirement.is_text_verifiable,
        citations=citations,
        conditions=conditions,
    )


def build_synthetic_requirements(
    fixture: TrueRequirementsFixture,
) -> list[Requirement]:
    return [_synthetic_requirement(r) for r in fixture.requirements]


class VerdictOnlyOutcome(BaseModel):
    topic_id: str
    requirement_text: str
    predicted_verdict: str
    acceptable_verdicts: list[str] | None
    is_correct: bool
    # primary_verdict is the single distilled/fallback training-target
    # label (see evaluation/fixtures.py TrueVerdict.primary_verdict) --
    # matching it is a strictly harder bar than acceptable_verdicts
    # membership (acceptable_verdicts is often a 2-element set; primary
    # is exactly one of those). Reported alongside, not instead of, the
    # acceptable_verdicts-based figure -- they answer different questions
    # ("is this a defensible verdict" vs "does this match the specific
    # label SFT trains toward") and should never be quoted interchangeably.
    primary_verdict: str | None = None
    is_correct_vs_primary: bool | None = None
    evidence_quotes: list[str]
    reasoning: str
    true_rationale: str
    true_evidence_quotes: list[str]
    retrieved_context: list[str]


class VerdictOnlyResult(BaseModel):
    accuracy: float
    scored_topic_count: int
    accuracy_vs_primary: float | None = None
    scored_topic_count_vs_primary: int = 0
    outcomes: list[VerdictOnlyOutcome]
    mismatches: list[VerdictOnlyOutcome]


def _acceptable_verdicts_by_topic(
    fixture: TrueVerdictsFixture,
) -> dict[str, list[str] | None]:
    acceptable = {}
    for verdict in fixture.verdicts:
        acceptable[verdict.topic_id] = verdict.acceptable_verdicts
    return acceptable


def _primary_verdict_by_topic(
    fixture: TrueVerdictsFixture,
) -> dict[str, str | None]:
    primary = {}
    for verdict in fixture.verdicts:
        primary[verdict.topic_id] = verdict.primary_verdict
    return primary


def _true_rationale_by_topic(fixture: TrueVerdictsFixture) -> dict[str, str]:
    rationale = {}
    for verdict in fixture.verdicts:
        rationale[verdict.topic_id] = verdict.rationale
    return rationale


def _true_evidence_by_topic(
    fixture: TrueVerdictsFixture,
) -> dict[str, list[str]]:
    evidence_by_topic = {}
    for verdict in fixture.verdicts:
        evidence_by_topic[verdict.topic_id] = [
            evidence.quote for evidence in verdict.evidence
        ]
    return evidence_by_topic


def _evidence_quotes(verdict: Verdict) -> list[str]:
    quotes = []
    for evidence in verdict.evidence:
        quotes.append(evidence.quote)
    return quotes


def _retrieved_context_by_requirement(
    retrieved_evidence: list[RetrievedEvidenceRecord],
) -> dict[str, list[str]]:
    by_requirement = retrieved_by_requirement(retrieved_evidence)
    context = {}
    for requirement_id, chunks in by_requirement.items():
        context[requirement_id] = [chunk.text for chunk in chunks]
    return context


def score_verdicts(
    predicted_verdicts: list[Verdict],
    verdicts_fixture: TrueVerdictsFixture,
    retrieved_evidence: list[RetrievedEvidenceRecord] | None = None,
) -> VerdictOnlyResult:
    acceptable_by_topic = _acceptable_verdicts_by_topic(verdicts_fixture)
    primary_by_topic = _primary_verdict_by_topic(verdicts_fixture)
    rationale_by_topic = _true_rationale_by_topic(verdicts_fixture)
    true_evidence_by_topic = _true_evidence_by_topic(verdicts_fixture)
    retrieved_context_by_requirement = _retrieved_context_by_requirement(
        retrieved_evidence or []
    )
    outcomes = []
    for verdict in predicted_verdicts:
        topic_id = verdict.requirement_id
        acceptable = acceptable_by_topic.get(topic_id)
        if acceptable is None:
            continue
        primary = primary_by_topic.get(topic_id)
        outcomes.append(VerdictOnlyOutcome(
            topic_id=topic_id,
            requirement_text=verdict.requirement_text,
            predicted_verdict=verdict.verdict.value,
            acceptable_verdicts=acceptable,
            is_correct=verdict.verdict.value in acceptable,
            primary_verdict=primary,
            is_correct_vs_primary=(
                verdict.verdict.value == primary
                if primary is not None else None
            ),
            evidence_quotes=_evidence_quotes(verdict),
            reasoning=verdict.reasoning,
            true_rationale=rationale_by_topic.get(topic_id, ""),
            true_evidence_quotes=true_evidence_by_topic.get(topic_id, []),
            retrieved_context=retrieved_context_by_requirement.get(
                topic_id, []
            ),
        ))
    mismatches = [outcome for outcome in outcomes if not outcome.is_correct]
    total = len(outcomes)
    correct = total - len(mismatches)
    accuracy = correct / total if total > 0 else 0.0
    primary_scored = [o for o in outcomes if o.is_correct_vs_primary is not None]
    accuracy_vs_primary = (
        sum(1 for o in primary_scored if o.is_correct_vs_primary)
        / len(primary_scored)
        if primary_scored else None
    )
    return VerdictOnlyResult(
        accuracy=accuracy,
        scored_topic_count=total,
        accuracy_vs_primary=accuracy_vs_primary,
        scored_topic_count_vs_primary=len(primary_scored),
        outcomes=outcomes,
        mismatches=mismatches,
    )


def _collapse_whitespace(text: str) -> str:
    return " ".join(text.split())


def _render_outcome(outcome: VerdictOnlyOutcome) -> list[str]:
    lines = [
        f"- `{outcome.topic_id}` — acceptable: "
        f"{outcome.acceptable_verdicts}, predicted: "
        f"{outcome.predicted_verdict}",
        f'  - **requirement:** "{_collapse_whitespace(outcome.requirement_text)}"',
    ]
    if not outcome.retrieved_context:
        lines.append("  - **retrieved context (shown to the model):** none")
    for chunk_text in outcome.retrieved_context:
        lines.append(
            f'  - **retrieved context (shown to the model):** '
            f'"{_collapse_whitespace(chunk_text)}"'
        )
    if outcome.evidence_quotes:
        for quote in outcome.evidence_quotes:
            lines.append(
                f"  - **model's evidence (what it chose to cite):** "
                f'"{_collapse_whitespace(quote)}"'
            )
    else:
        lines.append(
            "  - **model's evidence (what it chose to cite):** none"
        )
    if outcome.reasoning:
        lines.append(
            f"  - **model's reasoning:** "
            f"{_collapse_whitespace(outcome.reasoning)}"
        )
    if not outcome.true_evidence_quotes:
        lines.append("  - **expected evidence (true_verdicts.json):** none")
    for quote in outcome.true_evidence_quotes:
        lines.append(
            f'  - **expected evidence (true_verdicts.json):** '
            f'"{_collapse_whitespace(quote)}"'
        )
    if outcome.true_rationale:
        lines.append(
            f"  - **expected reasoning (true_verdicts.json):** "
            f"{_collapse_whitespace(outcome.true_rationale)}"
        )
    return lines


def render_verdict_only_report(result: VerdictOnlyResult) -> str:
    lines = ["## Verdict-only evaluation", ""]
    lines.append(
        "Runs verdict generation directly on true_requirements.json's own "
        "text and citations against application.txt, bypassing requirement "
        "extraction and match-group sequencing entirely -- isolates "
        "whether generate_verdict, given a perfect requirement, makes the "
        "right call. Only mismatches are listed below."
    )
    lines.append("")
    correct = result.scored_topic_count - len(result.mismatches)
    lines.append(
        f"**Accuracy vs acceptable_verdicts (any listed verdict counts): "
        f"{result.accuracy * 100:.1f}% ({correct}/{result.scored_topic_count})**"
    )
    if result.accuracy_vs_primary is not None:
        primary_correct = round(
            result.accuracy_vs_primary * result.scored_topic_count_vs_primary
        )
        lines.append(
            f"**Accuracy vs primary_verdict (single distilled/fallback "
            f"label, the SFT training target -- a strictly harder bar): "
            f"{result.accuracy_vs_primary * 100:.1f}% "
            f"({primary_correct}/{result.scored_topic_count_vs_primary})**"
        )
    lines.append("")
    if not result.mismatches:
        lines.append("- none")
    for outcome in result.mismatches:
        lines.extend(_render_outcome(outcome))
        lines.append("")
    return "\n".join(lines)
