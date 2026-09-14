"""DPO for the verdict-generation step, continuing from the merged SFT
checkpoint (see merge_sft_adapter.py). Reads sft/data/dpo_train.jsonl
built by build_dpo_dataset.py.

Architecture (see the "DPO planning" discussion this was built from):
- The merged SFT weights (base + old LoRA, already flattened into plain
  weights by merge_sft_adapter.py) are loaded as the base model here and
  never modified directly.
- A brand-new LoRA adapter is attached on top via `peft_config` passed
  straight into DPOTrainer, NOT pre-wrapped with get_peft_model. This
  matters: DPOTrainer raises if you hand it an already-PEFT-wrapped
  model together with a peft_config (see trl's dpo_trainer.py -- "please
  first merge and unload the existing adapter"). Passed this way,
  DPOTrainer wraps the model itself and, seeing `ref_model=None` and
  `is_peft_model(self.model) == True`, never loads a second copy of the
  weights for the reference -- it recovers the reference behavior by
  disabling the new adapter for that forward pass. That disabled state
  is exactly the merged SFT model, i.e. exactly the frozen reference we
  want, at no extra VRAM cost.
- This gives a DPO adapter that can be compared against the SFT-only
  adapter by simply swapping which adapter vLLM loads at eval time --
  no separate "did DPO help" ambiguity from retraining SFT itself.

Runs in the WSL venv at /root/sft/venv, same as train_verdict_lora.py.
"""
import json
import os

import torch
from datasets import Dataset
from peft import LoraConfig
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainerCallback,
)
from trl import DPOConfig, DPOTrainer

from sft.train_verdict_lora import TOOL_SCHEMA

MERGED_MODEL_DIR = "sft/checkpoints/verdict-lora-merged"
DATA_PATH = "sft/data/dpo_train.jsonl"
OUTPUT_DIR = "sft/checkpoints/verdict-dpo-lora"
MAX_SEQ_LEN = 2304

# Same beta as trl's own DPOConfig default: a mid-range value, deliberately
# not tuned for this proof-of-concept -- see the DPO options discussion.
DPO_BETA = 0.1


def load_jsonl(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _tool_call_message(completion: dict) -> dict:
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [{
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "submit_verdict",
                "arguments": json.dumps(completion, ensure_ascii=False),
            },
        }],
    }


def to_dpo_chat_example(row: dict) -> dict:
    """One dpo_train.jsonl row -> the {prompt, chosen, rejected, tools}
    conversational shape trl's DPOTrainer expects (see
    trl.trainer.dpo_trainer's tokenize_fn: prompt/chosen/rejected are each
    a list of chat messages, tools is passed straight through as an
    apply_chat_template kwarg)."""
    return {
        "prompt": [{"role": "user", "content": row["prompt"]}],
        "chosen": [_tool_call_message(row["chosen"])],
        "rejected": [_tool_call_message(row["rejected"])],
        "tools": [TOOL_SCHEMA],
        "topic_id": row["topic_id"],
        "case": row["case"],
    }


def build_dataset() -> Dataset:
    rows = [to_dpo_chat_example(r) for r in load_jsonl(DATA_PATH)]
    return Dataset.from_list(rows)


def load_model_and_tokenizer():
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(MERGED_MODEL_DIR)
    model = AutoModelForCausalLM.from_pretrained(
        MERGED_MODEL_DIR,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
    )
    return model, tokenizer


def build_lora_config() -> LoraConfig:
    # Same shape as the SFT adapter (sft/train_verdict_lora.py) -- a new,
    # independent adapter, not a continuation of the SFT one.
    return LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.1,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        task_type="CAUSAL_LM",
    )


class LossLogger(TrainerCallback):
    """Minimal loss_log.jsonl writer, same convention as
    train_verdict_lora.py's TaskMetricEarlyStopping.on_log, without the
    task-metric eval loop -- that would need a live inference server for
    the validation split, out of scope for this proof-of-concept."""

    def __init__(self, path: str):
        self.path = path

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs is None:
            return control
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"step": state.global_step, **logs}) + "\n")
        return control


def build_trainer(
    model,
    tokenizer,
    train_dataset: Dataset,
    lora_config: LoraConfig | None = None,
    output_dir: str | None = None,
    bf16: bool = True,
    gradient_checkpointing: bool = True,
) -> DPOTrainer:
    """lora_config/output_dir/bf16/gradient_checkpointing are overridable
    so tests can wire this same function up with a tiny CPU stand-in
    model (whose module names don't match build_lora_config()'s Qwen
    target_modules, and whose host may not support bf16) and a
    throwaway output dir, without touching sft/checkpoints/verdict-dpo-lora."""
    dpo_config = DPOConfig(
        output_dir=output_dir or OUTPUT_DIR,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        gradient_checkpointing=gradient_checkpointing,
        learning_rate=5e-6,
        num_train_epochs=1,
        beta=DPO_BETA,
        logging_steps=5,
        save_strategy="no",
        max_length=MAX_SEQ_LEN,
        bf16=bf16,
        report_to=[],
    )
    return DPOTrainer(
        model=model,
        ref_model=None,
        args=dpo_config,
        train_dataset=train_dataset,
        processing_class=tokenizer,
        peft_config=lora_config or build_lora_config(),
    )


def main():
    train_ds = build_dataset()
    print(f"DPO train examples: {len(train_ds)}")

    model, tokenizer = load_model_and_tokenizer()
    trainer = build_trainer(model, tokenizer, train_ds)
    trainer.add_callback(LossLogger(f"{OUTPUT_DIR}/loss_log.jsonl"))
    trainer.train()

    final_dir = f"{OUTPUT_DIR}/final"
    trainer.model.save_pretrained(final_dir)
    tokenizer.save_pretrained(final_dir)
    print(f"Saved DPO LoRA adapter to {final_dir}")


if __name__ == "__main__":
    main()
