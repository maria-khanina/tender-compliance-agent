"""Fully fine-tune the small verdict model with DeepSpeed ZeRO stage 2.

All weights are trained in bf16; with the offload configuration the fp32
master weights and Adam moments live in CPU memory and the optimizer step runs
there (DeepSpeed CPUAdam). The run records the validation macro F1 history,
peak GPU memory, peak host memory and seconds per optimizer step.

Usage (one process, launched by slurm/submit_full_fine_tuning.sh):
  python -m sft.train_full_zero --deepspeed-config sft/deepspeed_zero2_offload.json \
      --max-steps -1 --run-name zero2_offload
"""
import argparse
from dataclasses import dataclass, field
import json
import os
import statistics
import time

import psutil
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizerBase,
    TrainerCallback,
    TrainerControl,
    TrainerState,
    TrainingArguments,
)
from trl import SFTConfig, SFTTrainer  # type: ignore[reportPrivateImportUsage]

from sft.full_fine_tuning_settings import (
    ACCUMULATION_STEPS,
    BYTES_PER_GIBIBYTE,
    EARLY_STOP_MINIMUM_DELTA,
    EARLY_STOP_PATIENCE,
    EPOCHS,
    EVALUATE_EVERY_STEPS,
    FULL_MODEL,
    FULL_RUN_DIRECTORY,
    LEARNING_RATE,
    LOGGING_STEPS,
    MAXIMUM_SEQUENCE_LENGTH,
    MICRO_BATCH_SIZE,
    WARMUP_OPTIMIZER_STEPS,
    WEIGHT_DECAY,
)
from sft.train_verdict_lora import TaskMetricEarlyStopping, build_datasets


@dataclass
class QuietEarlyStopping(TaskMetricEarlyStopping):
    """Early stopping on validation macro F1 that never writes checkpoints."""

    def on_step_end(  # type: ignore[reportIncompatibleMethodOverride]
        self,
        training_arguments: TrainingArguments,
        state: TrainerState,
        control: TrainerControl,
        **extra: object,
    ) -> TrainerControl:
        """Evaluate as the parent does, then cancel any checkpoint save."""
        control = super().on_step_end(
            training_arguments,
            state,
            control,
            **extra,  # type: ignore[reportArgumentType]
        )
        control.should_save = False
        return control


@dataclass
class ResourceMonitor(TrainerCallback):
    """Record the duration of every optimizer step and peak host memory."""

    step_seconds: list[float] = field(default_factory=list)
    peak_host_bytes: int = 0
    started: float = 0.0

    def on_step_begin(  # type: ignore[reportIncompatibleMethodOverride]
        self,
        training_arguments: TrainingArguments,
        state: TrainerState,
        control: TrainerControl,
        **extra: object,
    ) -> TrainerControl:
        """Start the clock of an optimizer step."""
        torch.cuda.synchronize()
        self.started = time.perf_counter()
        return control

    def on_step_end(  # type: ignore[reportIncompatibleMethodOverride]
        self,
        training_arguments: TrainingArguments,
        state: TrainerState,
        control: TrainerControl,
        **extra: object,
    ) -> TrainerControl:
        """Stop the clock and update the peak resident memory of the process."""
        torch.cuda.synchronize()
        self.step_seconds.append(time.perf_counter() - self.started)
        resident = psutil.Process().memory_info().rss
        self.peak_host_bytes = max(self.peak_host_bytes, resident)
        return control


def parse_arguments() -> argparse.Namespace:
    """Read the DeepSpeed configuration, the step limit and the run name."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--deepspeed-config", required=True)
    parser.add_argument("--max-steps", type=int, required=True)
    parser.add_argument("--run-name", required=True)
    return parser.parse_args()


def load_model_and_tokenizer() -> tuple[PreTrainedModel, PreTrainedTokenizerBase]:
    """Load the small model in bf16 for full fine-tuning."""
    tokenizer = AutoTokenizer.from_pretrained(FULL_MODEL)
    model = AutoModelForCausalLM.from_pretrained(FULL_MODEL, dtype=torch.bfloat16)
    return model, tokenizer


def build_config(arguments: argparse.Namespace, run_directory: str) -> SFTConfig:
    """Describe the training run for TRL and the DeepSpeed integration."""
    return SFTConfig(
        output_dir=f"{run_directory}/checkpoints",
        deepspeed=arguments.deepspeed_config,
        per_device_train_batch_size=MICRO_BATCH_SIZE,
        gradient_accumulation_steps=ACCUMULATION_STEPS,
        gradient_checkpointing=True,
        learning_rate=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
        num_train_epochs=EPOCHS,
        max_steps=arguments.max_steps,
        logging_steps=LOGGING_STEPS,
        save_strategy="no",
        max_length=MAXIMUM_SEQUENCE_LENGTH,
        bf16=True,
        report_to=[],
        assistant_only_loss=True,
    )


def build_callbacks(
    tokenizer: PreTrainedTokenizerBase,
    run_directory: str,
) -> tuple[QuietEarlyStopping, ResourceMonitor]:
    """Create the early stopping and the resource monitor of one run."""
    _, validation_rows = build_datasets()
    early_stopping = QuietEarlyStopping(
        tokenizer=tokenizer,
        val_rows=validation_rows,
        patience=EARLY_STOP_PATIENCE,
        min_delta=EARLY_STOP_MINIMUM_DELTA,
        eval_every_n_steps=EVALUATE_EVERY_STEPS,
        save_every_n_steps=0,
        history_path=f"{run_directory}/validation_history.json",
        loss_log_path=f"{run_directory}/loss_log.jsonl",
    )
    return early_stopping, ResourceMonitor()


def summarize(
    early_stopping: QuietEarlyStopping,
    monitor: ResourceMonitor,
    out_of_memory: bool,
) -> dict[str, float | int | bool | None]:
    """Collect the measurements of a run into one record."""
    measured = monitor.step_seconds[WARMUP_OPTIMIZER_STEPS:]
    return {
        "out_of_memory": out_of_memory,
        "optimizer_steps": len(monitor.step_seconds),
        "seconds_per_step": statistics.mean(measured) if measured else None,
        "peak_gpu_gibibytes": torch.cuda.max_memory_allocated() / BYTES_PER_GIBIBYTE,
        "peak_host_gibibytes": monitor.peak_host_bytes / BYTES_PER_GIBIBYTE,
        "best_macro_f1": early_stopping.best_metric,
        "best_step": early_stopping.best_step,
    }


def build_trainer(
    arguments: argparse.Namespace,
    run_directory: str,
) -> tuple[SFTTrainer, QuietEarlyStopping, ResourceMonitor]:
    """Load the model and data and assemble the trainer with its callbacks."""
    model, tokenizer = load_model_and_tokenizer()
    train_dataset, _ = build_datasets()
    early_stopping, monitor = build_callbacks(tokenizer, run_directory)
    trainer = SFTTrainer(
        model=model,
        args=build_config(arguments, run_directory),
        train_dataset=train_dataset,
        processing_class=tokenizer,
        callbacks=[early_stopping, monitor],
    )
    return trainer, early_stopping, monitor


def train(arguments: argparse.Namespace, run_directory: str) -> None:
    """Run the training and write its summary next to the history."""
    trainer, early_stopping, monitor = build_trainer(arguments, run_directory)
    out_of_memory = False
    try:
        trainer.train()
    except torch.OutOfMemoryError:
        out_of_memory = True
    summary = summarize(early_stopping, monitor, out_of_memory)
    with open(f"{run_directory}/summary.json", "w", encoding="utf-8") as summary_file:
        json.dump(summary, summary_file, indent=2)
    print(json.dumps(summary, indent=2))


def main() -> None:
    """Train one configuration named on the command line."""
    arguments = parse_arguments()
    run_directory = f"{FULL_RUN_DIRECTORY}/{arguments.run_name}"
    os.makedirs(run_directory, exist_ok=True)
    train(arguments, run_directory)


if __name__ == "__main__":
    main()
