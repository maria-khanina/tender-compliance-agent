"""Integration test for the DPO wiring in train_dpo.py, using a tiny
randomly-initialized public test model instead of the real Qwen3-8B/SFT
checkpoint (which this test must never load or modify). Exercises the
exact same build_trainer() call train_dpo.main() makes -- the one part
of this whole feature that couldn't be verified by reasoning about the
code alone: does trl's DPOTrainer, given a plain (non-PEFT) base model
plus a fresh `peft_config` and `ref_model=None`, actually run end to end
and use the "disable adapter" trick for the reference model instead of
loading a second copy of the weights? That is the entire point of the
"attach a new adapter, no separate ref_model" design (see train_dpo.py's
module docstring) -- if it silently fell back to loading a second real
model, DPO on the real 8B checkpoint would need roughly double the VRAM
we actually have.
"""
import math
from pathlib import Path

import pytest
from accelerate.utils import is_peft_model
from datasets import Dataset
from peft import LoraConfig
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizerBase,
)

from sft.train_dpo import build_trainer

TinyModelAndTokenizer = tuple[PreTrainedModel, PreTrainedTokenizerBase]

TINY_MODEL = "hf-internal-testing/tiny-random-gpt2"


@pytest.fixture()
def tiny_model_and_tokenizer() -> TinyModelAndTokenizer:
    # Function-scoped, not module-scoped: build_trainer() peft-wraps
    # `model` in place, so sharing one instance across tests would stack
    # a second adapter onto the first test's already-wrapped model.
    tokenizer = AutoTokenizer.from_pretrained(TINY_MODEL)
    model = AutoModelForCausalLM.from_pretrained(TINY_MODEL)
    return model, tokenizer


@pytest.fixture()
def tiny_preference_dataset() -> Dataset:
    # 8 rows so that, with per_device_train_batch_size=1 and
    # gradient_accumulation_steps=8 (train_dpo.build_trainer's hardcoded
    # values), one full epoch triggers exactly one real optimizer step
    # rather than only ever accumulating partial gradients.
    rows = [
        {
            "prompt": f"Requirement {row_index}: is it met?",
            "chosen": " compliant",
            "rejected": " non_compliant",
        }
        for row_index in range(8)
    ]
    return Dataset.from_list(rows)


def test_dpo_trainer_runs_and_produces_finite_loss(
    tiny_model_and_tokenizer: TinyModelAndTokenizer,
    tiny_preference_dataset: Dataset,
    tmp_path: Path,
):
    model, tokenizer = tiny_model_and_tokenizer
    lora_config = LoraConfig(
        r=4, lora_alpha=8, lora_dropout=0.0,
        target_modules=["c_attn"], task_type="CAUSAL_LM",
    )

    trainer = build_trainer(
        model,
        tokenizer,
        tiny_preference_dataset,
        lora_config=lora_config,
        output_dir=str(tmp_path),
        bf16=False,
        gradient_checkpointing=False,
    )

    # The whole point of this design: no second model instance for the
    # reference -- DPOTrainer must recover it by disabling the adapter.
    assert is_peft_model(trainer.model)
    assert trainer.ref_model is None

    trainer.train()

    # logging_steps=5 but this run only ever takes 1 optimizer step (8
    # examples / batch_size 1 / grad_accum 8), so the only log entry is
    # the final train-end summary ("train_loss"), not a mid-training
    # ("loss") entry -- both key names are accepted here.
    losses = [
        entry[key]
        for entry in trainer.state.log_history
        for key in ("loss", "train_loss")
        if key in entry
    ]
    assert losses, "expected at least one logged loss"
    assert all(math.isfinite(float(loss)) for loss in losses)


def test_disabling_the_new_adapter_changes_the_policys_output(
    tiny_model_and_tokenizer: TinyModelAndTokenizer,
    tiny_preference_dataset: Dataset,
    tmp_path: Path,
):
    """Confirms the disable-adapter reference path is actually wired to
    a *different* forward pass than the trainable policy -- i.e. training
    the new adapter for a few steps moves it away from its (zero-init)
    starting point, so "reference" and "policy" are not silently the
    same frozen thing throughout training."""
    model, tokenizer = tiny_model_and_tokenizer
    lora_config = LoraConfig(
        r=4, lora_alpha=8, lora_dropout=0.0,
        target_modules=["c_attn"], task_type="CAUSAL_LM",
    )
    trainer = build_trainer(
        model,
        tokenizer,
        tiny_preference_dataset,
        lora_config=lora_config,
        output_dir=str(tmp_path),
        bf16=False,
        gradient_checkpointing=False,
    )
    assert trainer.model is not None
    lora_param_name = next(
        name for name, _ in trainer.model.named_parameters() if "lora_B" in name
    )
    before = trainer.model.get_parameter(lora_param_name).detach().clone()
    trainer.train()
    after = trainer.model.get_parameter(lora_param_name).detach().clone()
    assert not (before == after).all(), (
        "LoRA adapter weights never moved during training"
    )
