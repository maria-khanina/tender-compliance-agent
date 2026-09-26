import json
import math
import os
from dataclasses import dataclass, field

import torch
from datasets import Dataset
from peft import LoraConfig, PeftModel
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    PreTrainedModel,
    PreTrainedTokenizerBase,
    TrainerCallback,
    TrainerControl,
    TrainerState,
    TrainingArguments,
)
import trl.trainer.dpo_trainer as _dpo_trainer_module
from trl import DPOConfig, DPOTrainer  # type: ignore[reportPrivateImportUsage]

from sft.training_schemas import (
    ChatExample,
    DpoChatExample,
    EvalHistoryEntry,
    PreferencePair,
    VerdictCompletion,
)
from sft.training_config import (
    DPO_BETA,
    DPO_EVAL_EVERY_N_STEPS,
    DPO_GRADIENT_ACCUMULATION_STEPS,
    DPO_LEARNING_RATE,
    DPO_LOGGING_STEPS,
    DPO_MAX_SEQ_LEN,
    DPO_NUM_TRAIN_EPOCHS,
    DPO_PER_DEVICE_TRAIN_BATCH_SIZE,
    DPO_RUN_DIR,
    DPO_TRAIN_DATA_PATH,
    DPO_WEIGHT_DECAY,
    LORA_ALPHA,
    LORA_DROPOUT,
    LORA_RANK,
    LORA_TARGET_MODULES,
    MERGED_MODEL_DIR,
    VAL_DATA_PATH,
)

_dpo_trainer_module.entropy_from_logits = (  # type: ignore[reportPrivateImportUsage]
    lambda logits, chunk_size=128: torch.zeros(
        logits.shape[:-1], device=logits.device
    )
)

OUTPUT_DIR = f"{DPO_RUN_DIR}/dpo_checkpoints"


def load_jsonl(path: str) -> list[PreferencePair]:
    rows: list[PreferencePair] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _tool_call_message(completion: VerdictCompletion) -> dict[str, object]:
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


def to_dpo_chat_example(row: PreferencePair) -> DpoChatExample:
    from sft.train_verdict_lora import TOOL_SCHEMA

    return {
        "prompt": [{"role": "user", "content": row["prompt"]}],
        "chosen": [_tool_call_message(row["chosen"])],
        "rejected": [_tool_call_message(row["rejected"])],
        "tools": [TOOL_SCHEMA],
        "topic_id": row["topic_id"],
        "case": row["case"],
    }


def build_dataset() -> Dataset:
    rows = [to_dpo_chat_example(r) for r in load_jsonl(DPO_TRAIN_DATA_PATH)]
    return Dataset.from_list(rows)  # type: ignore[reportArgumentType]


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
    return LoraConfig(
        r=LORA_RANK,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=LORA_TARGET_MODULES,
        task_type="CAUSAL_LM",
    )


@dataclass
class BestCheckpointTracker(TrainerCallback):
    tokenizer: PreTrainedTokenizerBase
    val_rows: list[ChatExample]
    eval_every_n_steps: int
    history_path: str = f"{DPO_RUN_DIR}/dpo_training_history.json"
    best_metric: float = field(default=-1.0)
    best_step: int = field(default=-1)
    history: list[EvalHistoryEntry] = field(default_factory=list)

    def _persist_history(self) -> None:
        os.makedirs(DPO_RUN_DIR, exist_ok=True)
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2)

    def on_step_end(  # type: ignore[reportIncompatibleMethodOverride]
        self,
        args: TrainingArguments,
        state: TrainerState,
        control: TrainerControl,
        model: PreTrainedModel | PeftModel | None = None,
        **kwargs: object,
    ) -> TrainerControl:
        from sft.train_verdict_lora import evaluate_task_accuracy

        step = state.global_step
        if step == 0 or step % self.eval_every_n_steps != 0:
            return control
        assert model is not None, "Trainer always passes model to on_step_end"
        eval_result = evaluate_task_accuracy(model, self.tokenizer, self.val_rows)
        result: EvalHistoryEntry = {**eval_result, "step": step}
        self.history.append(result)
        self._persist_history()
        print(
            f"[dpo-eval] step={step} accuracy={result['task_accuracy']:.3f} "
            f"macro_f1={result['macro_f1']:.3f} (n={result['n']})"
        )
        if result["macro_f1"] > self.best_metric:
            self.best_metric = result["macro_f1"]
            self.best_step = step
            control.should_save = True
            print(
                f"[dpo-eval] new best macro_f1={result['macro_f1']:.3f} "
                "-- checkpoint saved"
            )
        return control


class LossLogger(TrainerCallback):
    def __init__(self, path: str):
        self.path = path

    def on_log(  # type: ignore[reportIncompatibleMethodOverride]
        self,
        args: TrainingArguments,
        state: TrainerState,
        control: TrainerControl,
        logs: dict[str, float] | None = None,
        **kwargs: object,
    ) -> TrainerControl:
        if logs is None:
            return control
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"step": state.global_step, **logs}) + "\n")
        return control


def build_trainer(
    model: PreTrainedModel | PeftModel,
    tokenizer: PreTrainedTokenizerBase,
    train_dataset: Dataset,
    lora_config: LoraConfig | None = None,
    output_dir: str | None = None,
    bf16: bool = True,
    gradient_checkpointing: bool = True,
) -> DPOTrainer:
    dpo_config = DPOConfig(
        output_dir=output_dir or OUTPUT_DIR,
        per_device_train_batch_size=DPO_PER_DEVICE_TRAIN_BATCH_SIZE,
        gradient_accumulation_steps=DPO_GRADIENT_ACCUMULATION_STEPS,
        gradient_checkpointing=gradient_checkpointing,
        learning_rate=DPO_LEARNING_RATE,
        weight_decay=DPO_WEIGHT_DECAY,
        num_train_epochs=DPO_NUM_TRAIN_EPOCHS,
        beta=DPO_BETA,
        logging_steps=DPO_LOGGING_STEPS,
        save_strategy="no",
        max_length=DPO_MAX_SEQ_LEN,
        bf16=bf16,
        report_to=[],
        use_liger_kernel=False,
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
    from sft.peft_utils import as_peft_model
    from sft.train_verdict_lora import load_jsonl as load_jsonl_sft
    from sft.train_verdict_lora import to_chat_example

    train_ds = build_dataset()
    val_rows = [to_chat_example(r) for r in load_jsonl_sft(VAL_DATA_PATH)]
    print(f"DPO train examples: {len(train_ds)}, validation examples: {len(val_rows)}")

    model, tokenizer = load_model_and_tokenizer()

    total_steps = math.ceil(
        len(train_ds)
        / (DPO_PER_DEVICE_TRAIN_BATCH_SIZE * DPO_GRADIENT_ACCUMULATION_STEPS)
    ) * DPO_NUM_TRAIN_EPOCHS
    print(
        f"total DPO steps ~= {total_steps}, "
        f"eval every {DPO_EVAL_EVERY_N_STEPS} steps"
    )

    checkpoint_tracker = BestCheckpointTracker(
        tokenizer=tokenizer,
        val_rows=val_rows,
        eval_every_n_steps=DPO_EVAL_EVERY_N_STEPS,
    )

    trainer = build_trainer(model, tokenizer, train_ds)
    trainer.add_callback(LossLogger(f"{DPO_RUN_DIR}/dpo_loss_log.jsonl"))
    trainer.add_callback(checkpoint_tracker)
    trainer.train()

    final_dir = f"{OUTPUT_DIR}/final"
    as_peft_model(trainer.model).save_pretrained(final_dir)
    tokenizer.save_pretrained(final_dir)
    print(f"Saved DPO LoRA adapter to {final_dir}")
    print(
        f"Best step: {checkpoint_tracker.best_step}, "
        f"best macro_f1: {checkpoint_tracker.best_metric:.3f}"
    )


if __name__ == "__main__":
    main()
