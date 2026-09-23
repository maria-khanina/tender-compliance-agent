import json
import pathlib

from pydantic import BaseModel

from schemas import Requirement, RetrievedContextRecord, Verdict


class SourceSpan(BaseModel):
    start_char: int
    end_char: int
    used_for_matching: bool = True


class TrueSource(BaseModel):
    document_path: str
    quote: str
    spans: list[SourceSpan]


class TrueRequirement(BaseModel):
    topic_id: str
    description: str
    is_mandatory: bool
    is_text_verifiable: bool
    source: TrueSource
    applicability_condition: TrueSource | None = None


class TrueRequirementsFixture(BaseModel):
    notes: list[str]
    requirements: list[TrueRequirement]


class TrueEvidenceSpan(BaseModel):
    document_path: str
    quote: str
    start_char: int
    end_char: int


class TrueVerdict(BaseModel):
    topic_id: str
    acceptable_verdicts: list[str] | None
    rationale: str
    evidence: list[TrueEvidenceSpan]
    primary_verdict: str | None = None
    primary_verdict_source: str | None = None
    condition_holds: bool | None = None


class TrueVerdictsFixture(BaseModel):
    notes: list[str]
    verdicts: list[TrueVerdict]


def _load_json(path: pathlib.Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def load_true_requirements(path: pathlib.Path) -> TrueRequirementsFixture:
    return TrueRequirementsFixture.model_validate(_load_json(path))


def load_true_verdicts(path: pathlib.Path) -> TrueVerdictsFixture:
    return TrueVerdictsFixture.model_validate(_load_json(path))


def load_predicted_requirements(path: pathlib.Path) -> list[Requirement]:
    payload = _load_json(path)
    assert isinstance(payload, list)
    return [Requirement.model_validate(item) for item in payload]


def load_predicted_verdicts(path: pathlib.Path) -> list[Verdict]:
    payload = _load_json(path)
    assert isinstance(payload, list)
    return [Verdict.model_validate(item) for item in payload]


def load_retrieved_context(
    path: pathlib.Path,
) -> list[RetrievedContextRecord]:
    payload = _load_json(path)
    assert isinstance(payload, list)
    return [RetrievedContextRecord.model_validate(item) for item in payload]
