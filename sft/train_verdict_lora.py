"""QLoRA SFT for the verdict-generation step (Qwen/Qwen3-8B, 4-bit base +
LoRA adapter -- served later on top of Qwen/Qwen3-8B-AWQ via vLLM
--enable-lora). Runs in the WSL venv at /root/sft/venv, not the main repo's
Python env. Reads sft/data/verdicts_*.jsonl from build_verdict_dataset.py.
"""
import json
import re
from dataclasses import dataclass, field

import torch
from datasets import Dataset
from peft import LoraConfig, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainerCallback,
)
from trl import SFTConfig, SFTTrainer

BASE_MODEL = "Qwen/Qwen3-8B"
DATA_DIR = "sft/data"
OUTPUT_DIR = "sft/checkpoints/verdict-lora"
MAX_SEQ_LEN = 2304

VERDICT_LABELS = [
    "compliant", "non_compliant", "insufficient_information", "contradictory",
]

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "submit_verdict",
        "description": "Submit the compliance verdict for this requirement.",
        "parameters": {
            "type": "object",
            "properties": {
                "verdict": {"type": "string", "enum": VERDICT_LABELS},
                "evidence_quotes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "chunk_index": {"type": "integer"},
                            "quote": {"type": "string"},
                            "role": {
                                "type": "string",
                                "enum": ["supports", "contradicts", "inconclusive"],
                            },
                        },
                        "required": ["chunk_index", "quote", "role"],
                    },
                },
                "reasoning": {"type": "string"},
            },
            "required": ["verdict", "evidence_quotes", "reasoning"],
        },
    },
}


def load_jsonl(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def to_chat_example(row: dict) -> dict:
    """One row -> {messages, tools} in the shape trl's SFTTrainer /
    tokenizer.apply_chat_template expects, with the assistant turn as a
    tool call so training-time formatting matches how vLLM will actually
    present/expect this model's output at inference time."""
    completion = row["completion"]
    tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {
            "name": "submit_verdict",
            "arguments": json.dumps(completion, ensure_ascii=False),
        },
    }
    return {
        "messages": [
            {"role": "user", "content": row["prompt"]},
            {"role": "assistant", "content": None, "tool_calls": [tool_call]},
        ],
        "tools": [TOOL_SCHEMA],
        "topic_id": row["topic_id"],
        "case": row["case"],
        "true_verdict": completion["verdict"],
    }


def build_datasets() -> tuple[Dataset, list[dict]]:
    train_rows = [
        to_chat_example(r)
        for r in load_jsonl(f"{DATA_DIR}/verdicts_train.jsonl")
    ]
    val_rows = [
        to_chat_example(r)
        for r in load_jsonl(f"{DATA_DIR}/verdicts_validation.jsonl")
    ]
    train_ds = Dataset.from_list(train_rows)
    return train_ds, val_rows


def load_model_and_tokenizer():
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
    )
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.1,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    return model, tokenizer


def extract_verdict_label(generated_text: str) -> str | None:
    """Best-effort parse of the model's tool-call arguments back to a
    verdict label -- used only for the validation task-metric, not for
    training. Handles both a clean JSON tool-call and a bare JSON object,
    since exact tool-call formatting can vary until the format is verified
    against a real generation."""
    match = re.search(r'"verdict"\s*:\s*"(\w+)"', generated_text)
    if match and match.group(1) in VERDICT_LABELS:
        return match.group(1)
    return None


@torch.no_grad()
def evaluate_task_accuracy(model, tokenizer, val_rows: list[dict]) -> dict:
    model.eval()
    correct = 0
    per_class = {label: {"tp": 0, "fp": 0, "fn": 0} for label in VERDICT_LABELS}
    for row in val_rows:
        prompt_messages = [row["messages"][0]]
        input_text = tokenizer.apply_chat_template(
            prompt_messages,
            tools=row["tools"],
            add_generation_prompt=True,
            tokenize=False,
        )
        inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
        output_ids = model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
        generated = tokenizer.decode(
            output_ids[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        )
        predicted = extract_verdict_label(generated)
        true_label = row["true_verdict"]
        if predicted == true_label:
            correct += 1
            per_class[true_label]["tp"] += 1
        else:
            per_class[true_label]["fn"] += 1
            if predicted in per_class:
                per_class[predicted]["fp"] += 1

    accuracy = correct / len(val_rows) if val_rows else 0.0
    f1_scores = []
    for label, counts in per_class.items():
        tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        if precision + recall:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = 0.0
        f1_scores.append(f1)
    macro_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0
    model.train()
    return {"task_accuracy": accuracy, "macro_f1": macro_f1, "n": len(val_rows)}


@dataclass
class TaskMetricEarlyStopping(TrainerCallback):
    tokenizer: object
    val_rows: list[dict]
    patience: int = 3
    min_delta: float = 0.01
    eval_every_n_steps: int = 40
    save_every_n_steps: int = 15
    history_path: str = f"{OUTPUT_DIR}/training_history.json"
    loss_log_path: str = f"{OUTPUT_DIR}/loss_log.jsonl"
    best_metric: float = field(default=-1.0)
    best_step: int = field(default=-1)
    rounds_without_improvement: int = field(default=0)
    history: list = field(default_factory=list)
    pending_metric: float | None = field(default=None)
    pending_step: int | None = field(default=None)

    def _persist_history(self) -> None:
        import os
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2)

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs is None:
            return control
        import os
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(self.loss_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"step": state.global_step, **logs}) + "\n")
        return control

    def on_step_end(self, args, state, control, model=None, **kwargs):
        step = state.global_step
        if step == 0:
            return control
        is_eval_step = step % self.eval_every_n_steps == 0
        is_periodic_save_step = (
            self.save_every_n_steps and step % self.save_every_n_steps == 0
        )
        if is_periodic_save_step and not is_eval_step:
            control.should_save = True
            print(f"[checkpoint] periodic save at step {step}")
        if not is_eval_step:
            return control
        result = evaluate_task_accuracy(model, self.tokenizer, self.val_rows)
        result["step"] = state.global_step
        self.history.append(result)
        self._persist_history()
        print(
            f"[task-eval] step={state.global_step} "
            f"accuracy={result['task_accuracy']:.3f} "
            f"macro_f1={result['macro_f1']:.3f} (n={result['n']})"
        )
        metric = result["macro_f1"]
        if metric > self.best_metric + self.min_delta:
            is_confirmation = (
                self.pending_metric is not None
                and step - self.pending_step == self.eval_every_n_steps
            )
            if is_confirmation:
                self.best_metric = metric
                self.best_step = step
                self.rounds_without_improvement = 0
                control.should_save = True
                self.pending_metric = None
                self.pending_step = None
                print(
                    f"[task-eval] confirmed new best macro_f1={metric:.3f} "
                    f"(improved for 2 consecutive rounds) -- checkpoint saved"
                )
            else:
                self.pending_metric = metric
                self.pending_step = step
                self.rounds_without_improvement = 0
                print(
                    f"[task-eval] possible improvement macro_f1={metric:.3f} "
                    f"-- not yet saved, awaiting confirmation next round"
                )
        else:
            self.pending_metric = None
            self.pending_step = None
            self.rounds_without_improvement += 1
            print(
                f"[task-eval] no improvement "
                f"({self.rounds_without_improvement}/{self.patience})"
            )
            if self.rounds_without_improvement >= self.patience:
                print(
                    f"[task-eval] stopping: no macro_f1 improvement for "
                    f"{self.patience} rounds. Best step={self.best_step} "
                    f"(macro_f1={self.best_metric:.3f})"
                )
                control.should_training_stop = True
        return control


def main():
    train_ds, val_rows = build_datasets()
    print(f"train examples: {len(train_ds)}, validation examples: {len(val_rows)}")

    model, tokenizer = load_model_and_tokenizer()

    early_stopping = TaskMetricEarlyStopping(
        tokenizer=tokenizer,
        val_rows=val_rows,
        patience=3,
        min_delta=0.01,
        eval_every_n_steps=40,
    )

    sft_config = SFTConfig(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        gradient_checkpointing=True,
        learning_rate=1e-4,
        num_train_epochs=6,
        logging_steps=10,
        save_strategy="no",
        max_length=MAX_SEQ_LEN,
        bf16=True,
        report_to=[],
        assistant_only_loss=True,
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=train_ds,
        processing_class=tokenizer,
        callbacks=[early_stopping],
    )
    trainer.train()

    final_dir = f"{OUTPUT_DIR}/final"
    trainer.model.save_pretrained(final_dir)
    tokenizer.save_pretrained(final_dir)
    print(f"Saved LoRA adapter to {final_dir}")
    print(f"Best step: {early_stopping.best_step}, "
          f"best macro_f1: {early_stopping.best_metric:.3f}")
    with open(f"{OUTPUT_DIR}/training_history.json", "w", encoding="utf-8") as f:
        json.dump(early_stopping.history, f, indent=2)


if __name__ == "__main__":
    main()
