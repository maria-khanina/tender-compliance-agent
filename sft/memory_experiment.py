"""Measure peak GPU memory and optimizer step time of one QLoRA SFT setup.

The model, 4-bit quantization and LoRA adapter come from the real SFT
script; the batch is real training text packed to a fixed length, so every
configuration processes the same number of tokens per micro-batch.

Usage:
  python -m sft.memory_experiment --configuration checkpointing_on_len1024_batch1
"""
import argparse
import json
import os
import statistics
import time
from typing import cast

from peft import PeftModel
import torch
from transformers import PreTrainedModel, PreTrainedTokenizerBase

from sft.memory_experiment_settings import (
    BYTES_PER_GIBIBYTE,
    LEARNING_RATE,
    MEASURED_OPTIMIZER_STEPS,
    MEMORY_CONFIGURATIONS,
    MEMORY_RESULTS_PATH,
    MEMORY_RUN_DIRECTORY,
    WARMUP_OPTIMIZER_STEPS,
    MemoryConfiguration,
    MemoryResult,
)
from sft.train_verdict_lora import load_jsonl, load_model_and_tokenizer
from sft.training_config import TRAIN_DATA_PATH


def parse_configuration_name() -> str:
    """Read the name of the configuration to measure from the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--configuration", required=True)
    return parser.parse_args().configuration


def find_configuration(name: str) -> MemoryConfiguration:
    """Return the configuration with the given name."""
    for configuration in MEMORY_CONFIGURATIONS:
        if configuration["name"] == name:
            return configuration
    raise ValueError(f"unknown configuration {name}")


def collect_token_ids(
    tokenizer: PreTrainedTokenizerBase,
    token_count: int,
) -> list[int]:
    """Tokenize training examples until token_count tokens are collected."""
    token_ids: list[int] = []
    for row in load_jsonl(TRAIN_DATA_PATH):
        text = row["prompt"] + json.dumps(row["completion"], ensure_ascii=False)
        token_ids.extend(tokenizer(text)["input_ids"])
        if len(token_ids) >= token_count:
            break
    return token_ids[:token_count]


def build_batch(
    tokenizer: PreTrainedTokenizerBase,
    configuration: MemoryConfiguration,
) -> torch.Tensor:
    """Pack real training tokens into one micro-batch on the GPU."""
    rows = configuration["micro_batch_size"]
    columns = configuration["sequence_length"]
    token_ids = collect_token_ids(tokenizer, rows * columns)
    return torch.tensor(token_ids, device="cuda").reshape(rows, columns)


def prepare_model(model: PeftModel, gradient_checkpointing: bool) -> None:
    """Switch the model to training mode with or without checkpointing."""
    base_model = cast(PreTrainedModel, model.get_base_model())
    if gradient_checkpointing:
        base_model.gradient_checkpointing_enable(
            gradient_checkpointing_kwargs={"use_reentrant": False},
        )
        base_model.enable_input_require_grads()
    base_model.config.use_cache = False
    model.train()


def run_optimizer_step(
    model: PeftModel,
    batch: torch.Tensor,
    optimizer: torch.optim.Optimizer,
    accumulation_steps: int,
) -> float:
    """Run one optimizer step over accumulated micro-batches; return seconds."""
    torch.cuda.synchronize()
    start = time.perf_counter()
    for _ in range(accumulation_steps):
        with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
            loss = model(input_ids=batch, labels=batch).loss / accumulation_steps
        loss.backward()
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)
    torch.cuda.synchronize()
    return time.perf_counter() - start


def to_gibibytes(byte_count: int) -> float:
    """Convert bytes to gibibytes."""
    return byte_count / BYTES_PER_GIBIBYTE


def build_result(
    configuration: MemoryConfiguration,
    model: PeftModel,
    static_bytes: int,
    measured_seconds: list[float] | None,
) -> MemoryResult:
    """Combine the configuration, memory counters and timings into a result."""
    trainable_parameters, total_parameters = model.get_nb_trainable_parameters()
    tokens_per_step = (
        configuration["micro_batch_size"]
        * configuration["sequence_length"]
        * configuration["accumulation_steps"]
    )
    seconds = statistics.mean(measured_seconds) if measured_seconds else None
    return {
        **configuration,
        "out_of_memory": measured_seconds is None,
        "static_allocated_gibibytes": to_gibibytes(static_bytes),
        "peak_allocated_gibibytes": to_gibibytes(torch.cuda.max_memory_allocated()),
        "peak_reserved_gibibytes": to_gibibytes(torch.cuda.max_memory_reserved()),
        "seconds_per_optimizer_step": seconds,
        "tokens_per_second": tokens_per_step / seconds if seconds else None,
        "trainable_parameters": trainable_parameters,
        "total_parameters": total_parameters,
    }


def build_optimizer(model: PeftModel) -> torch.optim.Optimizer:
    """Create AdamW over the trainable LoRA parameters only."""
    trainable: list[torch.nn.Parameter] = [
        parameter for parameter in model.parameters() if parameter.requires_grad
    ]
    return torch.optim.AdamW(trainable, lr=LEARNING_RATE)


def run_steps(
    model: PeftModel,
    batch: torch.Tensor,
    optimizer: torch.optim.Optimizer,
    configuration: MemoryConfiguration,
) -> list[float]:
    """Run the warm-up and measured optimizer steps; return measured seconds."""
    step_count = WARMUP_OPTIMIZER_STEPS + MEASURED_OPTIMIZER_STEPS
    timings: list[float] = [
        run_optimizer_step(
            model,
            batch,
            optimizer,
            configuration["accumulation_steps"],
        )
        for _ in range(step_count)
    ]
    return timings[WARMUP_OPTIMIZER_STEPS:]


def measure(
    configuration: MemoryConfiguration,
    model: PeftModel,
    tokenizer: PreTrainedTokenizerBase,
) -> MemoryResult:
    """Train a few steps of one configuration and measure memory and time."""
    prepare_model(model, configuration["gradient_checkpointing"])
    batch = build_batch(tokenizer, configuration)
    optimizer = build_optimizer(model)
    static_bytes = torch.cuda.memory_allocated()
    torch.cuda.reset_peak_memory_stats()
    try:
        measured_seconds = run_steps(model, batch, optimizer, configuration)
    except torch.OutOfMemoryError:
        return build_result(configuration, model, static_bytes, None)
    return build_result(configuration, model, static_bytes, measured_seconds)


def append_result(result: MemoryResult) -> None:
    """Append one result as a JSON line to the shared results file."""
    os.makedirs(MEMORY_RUN_DIRECTORY, exist_ok=True)
    with open(MEMORY_RESULTS_PATH, "a", encoding="utf-8") as results_file:
        results_file.write(json.dumps(result) + "\n")


def main() -> None:
    """Measure the configuration named on the command line."""
    configuration = find_configuration(parse_configuration_name())
    model, tokenizer = load_model_and_tokenizer()
    result = measure(configuration, model, tokenizer)
    append_result(result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
