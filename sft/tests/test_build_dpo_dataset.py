from sft.build_dpo_dataset import build_preference_row


def _row(verdict="non_compliant"):
    return {
        "case": "case1",
        "variant": "canonical",
        "topic_id": "topic1",
        "prompt": "Requirement: ... Evidence: ...",
        "completion": {
            "verdict": verdict,
            "evidence_quotes": [
                {"chunk_index": 0, "quote": "gold quote", "role": "contradicts"}
            ],
            "reasoning": "gold reasoning",
        },
    }


def _sample(verdict, reasoning="sampled reasoning"):
    return {
        "verdict": verdict,
        "evidence_quotes": [
            {"chunk_index": 1, "quote": "sampled quote", "role": "supports"}
        ],
        "reasoning": reasoning,
    }


def test_returns_none_when_every_sample_matches_gold():
    row = _row(verdict="compliant")
    samples = [_sample("compliant"), _sample("compliant"), _sample("compliant")]
    assert build_preference_row(row, samples) is None


def test_returns_none_for_empty_sample_list():
    row = _row(verdict="compliant")
    assert build_preference_row(row, []) is None


def test_picks_first_mismatching_sample_as_rejected():
    row = _row(verdict="compliant")
    samples = [
        _sample("compliant"),
        _sample("non_compliant", reasoning="first wrong one"),
        _sample("contradictory", reasoning="second wrong one"),
    ]
    pair = build_preference_row(row, samples)
    assert pair is not None
    assert pair["rejected"]["verdict"] == "non_compliant"
    assert pair["rejected"]["reasoning"] == "first wrong one"


def test_chosen_is_the_untouched_gold_completion():
    row = _row(verdict="insufficient_information")
    samples = [_sample("compliant")]
    pair = build_preference_row(row, samples)
    assert pair["chosen"] == row["completion"]


def test_rejected_reasoning_is_the_models_own_text_not_a_template():
    """The whole point of on-policy sampling: the rejected completion's
    reasoning must be exactly what the model itself generated to justify
    its (wrong) verdict, never a stitched-together template that argues
    for a different label than the one in "verdict". A future change
    that starts synthesizing rejected["reasoning"] instead of passing the
    sample through untouched would silently reintroduce that risk."""
    row = _row(verdict="compliant")
    samples = [_sample("non_compliant", reasoning="the model's own real argument")]
    pair = build_preference_row(row, samples)
    assert pair["rejected"]["reasoning"] == "the model's own real argument"


def test_metadata_carried_over_from_row():
    row = _row(verdict="compliant")
    samples = [_sample("non_compliant")]
    pair = build_preference_row(row, samples)
    assert pair["case"] == "case1"
    assert pair["variant"] == "canonical"
    assert pair["topic_id"] == "topic1"
    assert pair["prompt"] == row["prompt"]


def test_accepts_pydantic_like_objects_not_just_plain_dicts():
    """build_negative_samples() returns real VerdictResult pydantic
    objects in production; this exercises the same code path with a
    lightweight stand-in so the test doesn't need the full pipeline's
    dependencies."""

    class FakeLabel:
        def __init__(self, value):
            self.value = value

    class FakeQuote:
        def __init__(self, **kwargs):
            self._data = kwargs

        def model_dump(self):
            return self._data

    class FakeVerdictResult:
        def __init__(self, verdict, reasoning):
            self.verdict = FakeLabel(verdict)
            self.evidence_quotes = [
                FakeQuote(chunk_index=2, quote="q", role="supports")
            ]
            self.reasoning = reasoning

    row = _row(verdict="compliant")
    samples = [FakeVerdictResult("contradictory", "pydantic-shaped reasoning")]
    pair = build_preference_row(row, samples)
    assert pair["rejected"]["verdict"] == "contradictory"
    assert pair["rejected"]["reasoning"] == "pydantic-shaped reasoning"
    assert pair["rejected"]["evidence_quotes"] == [
        {"chunk_index": 2, "quote": "q", "role": "supports"}
    ]
