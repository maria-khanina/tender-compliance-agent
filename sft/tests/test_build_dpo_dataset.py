from sft.build_dpo_dataset import build_preference_rows, merge_row_pairs


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


def test_returns_empty_list_when_every_sample_matches_gold():
    row = _row(verdict="compliant")
    samples = [_sample("compliant"), _sample("compliant"), _sample("compliant")]
    assert build_preference_rows(row, samples) == []


def test_returns_empty_list_for_empty_sample_list():
    row = _row(verdict="compliant")
    assert build_preference_rows(row, []) == []


def test_one_pair_per_distinct_wrong_verdict():
    row = _row(verdict="compliant")
    samples = [
        _sample("compliant"),
        _sample("non_compliant", reasoning="first wrong one"),
        _sample("contradictory", reasoning="second wrong one"),
    ]
    pairs = build_preference_rows(row, samples)
    assert [p["rejected"]["verdict"] for p in pairs] == [
        "non_compliant", "contradictory",
    ]
    assert pairs[0]["rejected"]["reasoning"] == "first wrong one"
    assert pairs[1]["rejected"]["reasoning"] == "second wrong one"


def test_repeated_wrong_verdict_only_kept_once():
    """Same wrong label sampled twice must not produce two near-duplicate
    pairs sharing the same chosen -- only the first occurrence of each
    distinct wrong verdict is kept."""
    row = _row(verdict="compliant")
    samples = [
        _sample("non_compliant", reasoning="first phrasing"),
        _sample("non_compliant", reasoning="second phrasing"),
    ]
    pairs = build_preference_rows(row, samples)
    assert len(pairs) == 1
    assert pairs[0]["rejected"]["reasoning"] == "first phrasing"


def test_up_to_three_pairs_when_all_wrong_labels_appear():
    row = _row(verdict="compliant")
    samples = [
        _sample("non_compliant"),
        _sample("insufficient_information"),
        _sample("contradictory"),
    ]
    pairs = build_preference_rows(row, samples)
    assert len(pairs) == 3


def test_chosen_is_the_untouched_gold_completion():
    row = _row(verdict="insufficient_information")
    samples = [_sample("compliant")]
    pairs = build_preference_rows(row, samples)
    assert len(pairs) == 1
    assert pairs[0]["chosen"] == row["completion"]


def test_rejected_reasoning_is_the_models_own_text_not_a_template():
    """The whole point of on-policy sampling: the rejected completion's
    reasoning must be exactly what the model itself generated to justify
    its (wrong) verdict, never a stitched-together template that argues
    for a different label than the one in "verdict". A future change
    that starts synthesizing rejected["reasoning"] instead of passing the
    sample through untouched would silently reintroduce that risk."""
    row = _row(verdict="compliant")
    samples = [_sample("non_compliant", reasoning="the model's own real argument")]
    pairs = build_preference_rows(row, samples)
    assert len(pairs) == 1
    assert pairs[0]["rejected"]["reasoning"] == "the model's own real argument"


def test_metadata_carried_over_from_row():
    row = _row(verdict="compliant")
    samples = [_sample("non_compliant")]
    pairs = build_preference_rows(row, samples)
    assert len(pairs) == 1
    pair = pairs[0]
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
    pairs = build_preference_rows(row, samples)
    assert len(pairs) == 1
    pair = pairs[0]
    assert pair["rejected"]["verdict"] == "contradictory"
    assert pair["rejected"]["reasoning"] == "pydantic-shaped reasoning"
    assert pair["rejected"]["evidence_quotes"] == [
        {"chunk_index": 2, "quote": "q", "role": "supports"}
    ]


def _pair(row, wrong_verdict, reasoning="prior run's reasoning"):
    """An already-on-file pair, shaped exactly like a build_preference_rows
    result -- what a prior run's --output would contain for this row."""
    return {
        "case": row["case"],
        "variant": row["variant"],
        "topic_id": row["topic_id"],
        "prompt": row["prompt"],
        "chosen": row["completion"],
        "rejected": {
            "verdict": wrong_verdict,
            "evidence_quotes": [],
            "reasoning": reasoning,
        },
    }


def test_merge_keeps_existing_pair_when_no_new_samples():
    row = _row(verdict="compliant")
    existing = [_pair(row, "non_compliant")]
    assert merge_row_pairs(existing, row, []) == existing


def test_merge_adds_new_distinct_wrong_verdict_not_seen_before():
    row = _row(verdict="compliant")
    existing = [_pair(row, "non_compliant")]
    samples = [_sample("contradictory", reasoning="freshly sampled")]
    merged = merge_row_pairs(existing, row, samples)
    assert [p["rejected"]["verdict"] for p in merged] == [
        "non_compliant", "contradictory",
    ]
    assert merged[0] is existing[0]


def test_merge_does_not_duplicate_a_wrong_verdict_already_on_file():
    """The exact scenario a real re-run hits: a fresh sample reproduces a
    wrong verdict the previous run already found for this row. It must
    not be appended again as a second, near-identical pair."""
    row = _row(verdict="compliant")
    existing = [_pair(row, "non_compliant", reasoning="old phrasing")]
    samples = [_sample("non_compliant", reasoning="new phrasing, same label")]
    merged = merge_row_pairs(existing, row, samples)
    assert len(merged) == 1
    assert merged[0]["rejected"]["reasoning"] == "old phrasing"


def test_merge_from_empty_existing_matches_build_preference_rows():
    row = _row(verdict="compliant")
    samples = [_sample("non_compliant"), _sample("contradictory")]
    assert merge_row_pairs([], row, samples) == build_preference_rows(row, samples)


def test_merge_never_finding_anything_new_is_distinguishable_from_a_bug():
    """Guards the exact real-world result that prompted this test file:
    a top-up run whose fresh samples never disagree with the gold verdict
    must faithfully return just the existing pairs, unchanged -- not an
    empty list (which would silently look like "no pairs for this row"
    to the caller) and not a mutated copy of `existing`."""
    row = _row(verdict="compliant")
    existing = [_pair(row, "non_compliant")]
    all_matching_samples = [_sample("compliant"), _sample("compliant")]
    merged = merge_row_pairs(existing, row, all_matching_samples)
    assert merged == existing
    assert merged is not existing  # a fresh list, not the same object
