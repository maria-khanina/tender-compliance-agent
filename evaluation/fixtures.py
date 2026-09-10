import json
import pathlib

from pydantic import BaseModel

from schemas import Requirement, RetrievedEvidenceRecord, Verdict


class ExpectedSource(BaseModel):
    document_path: str
    quote: str
    start_char: int
    end_char: int


class ExpectedRequirement(BaseModel):
    topic_id: str
    description: str
    is_mandatory: bool
    source: ExpectedSource


class ExcludedClause(BaseModel):
    clause_id: str
    description: str
    source: ExpectedSource


class ExpectedRequirementsFixture(BaseModel):
    notes: list[str]
    requirements: list[ExpectedRequirement]
    excluded_clauses: list[ExcludedClause]


class ExpectedEvidenceSpan(BaseModel):
    document_path: str
    quote: str
    start_char: int
    end_char: int


class ExpectedVerdict(BaseModel):
    topic_id: str
    acceptable_verdicts: list[str] | None
    rationale: str
    evidence: list[ExpectedEvidenceSpan]


class ExpectedVerdictsFixture(BaseModel):
    notes: list[str]
    verdicts: list[ExpectedVerdict]


def _load_json(path: pathlib.Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def load_expected_requirements(
    path: pathlib.Path,
) -> ExpectedRequirementsFixture:
    return ExpectedRequirementsFixture.model_validate(_load_json(path))


def load_expected_verdicts(path: pathlib.Path) -> ExpectedVerdictsFixture:
    return ExpectedVerdictsFixture.model_validate(_load_json(path))


def load_actual_requirements(path: pathlib.Path) -> list[Requirement]:
    payload = _load_json(path)
    assert isinstance(payload, list)
    return [Requirement.model_validate(item) for item in payload]


def load_actual_verdicts(path: pathlib.Path) -> list[Verdict]:
    payload = _load_json(path)
    assert isinstance(payload, list)
    return [Verdict.model_validate(item) for item in payload]


def load_retrieved_evidence(
    path: pathlib.Path,
) -> list[RetrievedEvidenceRecord]:
    payload = _load_json(path)
    assert isinstance(payload, list)
    return [RetrievedEvidenceRecord.model_validate(item) for item in payload]
