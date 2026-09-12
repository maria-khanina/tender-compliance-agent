from evaluation.matching import MatchGroup
from evaluation.verdict_metrics import compute_verdict_accuracy


def _group(
    shape: str,
    true_topic_ids: list[str],
    predicted_node_ids: list[str],
) -> MatchGroup:
    return MatchGroup(
        true_topic_ids=true_topic_ids,
        predicted_node_ids=predicted_node_ids,
        shape=shape,
    )


def test_false_compliant_flagged_when_only_issue_verdicts_acceptable() -> None:
    groups = [_group("clean", ["topic_a"], ["req_1"])]
    acceptable = {"topic_a": ["non_compliant"]}
    predicted = {"req_1": "compliant"}
    result = compute_verdict_accuracy(groups, acceptable, predicted)
    assert result.false_compliant_rate == 1.0
    assert result.false_issue_rate == 0.0


def test_compliant_in_acceptable_list_does_not_count_as_false_compliant() -> None:
    groups = [_group("clean", ["topic_a"], ["req_1"])]
    acceptable = {"topic_a": ["compliant", "insufficient_information"]}
    predicted = {"req_1": "compliant"}
    result = compute_verdict_accuracy(groups, acceptable, predicted)
    assert result.false_compliant_rate == 0.0


def test_false_compliant_propagates_through_merge_group() -> None:
    groups = [_group("over_merge", ["topic_a", "topic_b"], ["req_1"])]
    acceptable = {
        "topic_a": ["compliant"],
        "topic_b": ["non_compliant"],
    }
    predicted = {"req_1": "compliant"}
    result = compute_verdict_accuracy(groups, acceptable, predicted)
    assert result.false_compliant_rate == 1.0
    assert len(result.unscored_groups) == 1
    assert result.unscored_groups[0].true_topic_ids == [
        "topic_a", "topic_b",
    ]
    assert result.unscored_groups[0].predicted_node_ids == ["req_1"]


def test_split_group_with_one_missing_verdict_is_not_verifiable() -> None:
    groups = [_group("over_split", ["topic_a"], ["req_1", "req_2"])]
    acceptable = {"topic_a": ["compliant"]}
    predicted = {"req_1": "compliant"}
    result = compute_verdict_accuracy(groups, acceptable, predicted)
    assert len(result.not_verifiable_groups) == 1
    assert result.not_verifiable_groups[0].true_topic_ids == ["topic_a"]
    assert result.not_verifiable_groups[0].predicted_node_ids == [
        "req_1", "req_2",
    ]
    assert result.unscored_groups == []
    assert result.false_compliant_rate == 0.0
    assert result.false_issue_rate == 0.0


def test_false_issue_flagged_when_only_compliant_acceptable() -> None:
    groups = [_group("clean", ["topic_a"], ["req_1"])]
    acceptable = {"topic_a": ["compliant"]}
    predicted = {"req_1": "non_compliant"}
    result = compute_verdict_accuracy(groups, acceptable, predicted)
    assert result.false_issue_rate == 1.0
    assert result.false_compliant_rate == 0.0


def test_group_with_no_predicted_verdict_is_not_verifiable_not_scored() -> None:
    groups = [_group("clean", ["topic_a"], ["req_1"])]
    acceptable = {"topic_a": ["compliant"]}
    predicted: dict[str, str] = {}
    result = compute_verdict_accuracy(groups, acceptable, predicted)
    assert result.confusion_matrix == []
    assert result.false_compliant_rate == 0.0
    assert result.false_issue_rate == 0.0
    assert len(result.not_verifiable_groups) == 1
    assert result.not_verifiable_groups[0].true_topic_ids == ["topic_a"]
    assert result.not_verifiable_groups[0].predicted_node_ids == ["req_1"]
    assert result.unscored_groups == []


def test_unscored_null_acceptable_verdicts_excluded_from_scoring() -> None:
    groups = [_group("clean", ["topic_a"], ["req_1"])]
    acceptable: dict[str, list[str] | None] = {"topic_a": None}
    predicted = {"req_1": "compliant"}
    result = compute_verdict_accuracy(groups, acceptable, predicted)
    assert result.confusion_matrix == []
    assert result.false_compliant_rate == 0.0
    assert result.false_issue_rate == 0.0
