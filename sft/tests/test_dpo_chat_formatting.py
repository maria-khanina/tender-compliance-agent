import json

from sft.train_dpo import to_dpo_chat_example


def _row():
    return {
        "case": "case1",
        "topic_id": "topic1",
        "prompt": "Requirement: ... Evidence: ...",
        "chosen": {
            "verdict": "non_compliant",
            "evidence_quotes": [
                {"chunk_index": 0, "quote": "gold quote", "role": "contradicts"}
            ],
            "reasoning": "gold reasoning",
        },
        "rejected": {
            "verdict": "compliant",
            "evidence_quotes": [
                {"chunk_index": 1, "quote": "sampled quote", "role": "supports"}
            ],
            "reasoning": "sampled reasoning",
        },
    }


def test_prompt_is_a_single_user_message():
    example = to_dpo_chat_example(_row())
    assert example["prompt"] == [{"role": "user", "content": _row()["prompt"]}]


def test_chosen_and_rejected_are_single_assistant_tool_call_messages():
    example = to_dpo_chat_example(_row())
    for key in ("chosen", "rejected"):
        messages = example[key]
        assert len(messages) == 1
        assert messages[0]["role"] == "assistant"
        assert messages[0]["content"] is None
        assert len(messages[0]["tool_calls"]) == 1
        assert messages[0]["tool_calls"][0]["function"]["name"] == "submit_verdict"


def test_tool_call_arguments_round_trip_to_the_original_completion():
    row = _row()
    example = to_dpo_chat_example(row)
    for key in ("chosen", "rejected"):
        arguments_json = example[key][0]["tool_calls"][0]["function"]["arguments"]
        assert json.loads(arguments_json) == row[key]


def test_tools_schema_is_attached():
    example = to_dpo_chat_example(_row())
    assert len(example["tools"]) == 1
    assert example["tools"][0]["function"]["name"] == "submit_verdict"


def test_chosen_and_rejected_differ_only_in_content_not_shape():
    """Regression guard for the "templated rationale" risk discussed
    before writing this: chosen and rejected must be structurally
    identical (same message shape, same tool name) -- if they ever
    diverge in shape, DPO could learn to prefer/reject based on that
    structural difference instead of the actual verdict content."""
    example = to_dpo_chat_example(_row())
    chosen_msg, rejected_msg = example["chosen"][0], example["rejected"][0]
    assert chosen_msg.keys() == rejected_msg.keys()
    assert (
        chosen_msg["tool_calls"][0]["function"]["name"]
        == rejected_msg["tool_calls"][0]["function"]["name"]
    )
