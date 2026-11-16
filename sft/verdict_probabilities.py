"""Probability of every verdict of a case, read from the tokens of the model.

The answer is forced up to the value of the verdict field of the
submit_verdict tool call, rendered by the chat template exactly as in the
training texts. For each of the four verdicts the log-probabilities of its
tokens (with the closing quote) are summed, and a softmax over the four sums
gives one probability per verdict. The needs-review score of a case is one
minus the probability of compliant, so a reviewer can rank the requirements
and choose a threshold instead of taking the single generated verdict.
"""
from typing import cast

from peft import PeftModel
import torch
from transformers import PreTrainedModel, PreTrainedTokenizerBase

from sft.review_workload_settings import VERDICT_END, VERDICT_FIELD
from sft.train_verdict_lora import VERDICT_LABELS
from sft.training_schemas import ChatExample

VerdictModel = PreTrainedModel | PeftModel


def forced_prefix(tokenizer: PreTrainedTokenizerBase, row: ChatExample) -> str:
    """Return the rendered conversation cut right before the verdict value."""
    text = cast(
        str,
        tokenizer.apply_chat_template(
            row["messages"],  # type: ignore[reportArgumentType]
            tools=row["tools"],  # type: ignore[reportArgumentType]
            tokenize=False,
            enable_thinking=False,
        ),
    )
    return text[:text.rindex(VERDICT_FIELD) + len(VERDICT_FIELD)]


def answer_token_ids(
    tokenizer: PreTrainedTokenizerBase,
    prefix: str,
) -> list[list[int]]:
    """Return the token ids of the prefix followed by each verdict."""
    sequences: list[list[int]] = []
    for label in VERDICT_LABELS:
        encoded = tokenizer(prefix + label + VERDICT_END, add_special_tokens=False)
        sequences.append(cast(list[int], encoded["input_ids"]))
    return sequences


def shared_length(sequences: list[list[int]]) -> int:
    """Return the number of leading tokens that all sequences share."""
    length = 0
    shortest = min(len(sequence) for sequence in sequences)
    while length < shortest and all(
        sequence[length] == sequences[0][length] for sequence in sequences
    ):
        length += 1
    return length


@torch.no_grad()
def continuation_log_probability(
    model: VerdictModel,
    token_ids: list[int],
    start: int,
) -> float:
    """Return the summed log-probability of the tokens from start to the end."""
    device = cast(torch.device, model.device)
    inputs = torch.tensor([token_ids], device=device)
    kept = len(token_ids) - start + 1
    output = model(input_ids=inputs, logits_to_keep=kept)
    log_probabilities = torch.log_softmax(output.logits[0, :-1].float(), dim=-1)
    targets = inputs[0, start:, None]
    return float(log_probabilities.gather(1, targets).sum())


def verdict_probabilities(
    model: VerdictModel,
    tokenizer: PreTrainedTokenizerBase,
    row: ChatExample,
) -> dict[str, float]:
    """Return the probability of every verdict for one case."""
    sequences = answer_token_ids(tokenizer, forced_prefix(tokenizer, row))
    start = shared_length(sequences)
    totals: list[float] = []
    for sequence in sequences:
        totals.append(continuation_log_probability(model, sequence, start))
    probabilities = torch.softmax(torch.tensor(totals), dim=0).tolist()
    return dict(zip(VERDICT_LABELS, probabilities))
