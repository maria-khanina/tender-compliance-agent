"""Configurations and constants of the training memory and step-time experiment."""
from typing import TypedDict


class MemoryConfiguration(TypedDict):
    """One training setup whose peak GPU memory and step time are measured."""

    name: str
    gradient_checkpointing: bool
    sequence_length: int
    micro_batch_size: int
    accumulation_steps: int


class MemoryResult(TypedDict):
    """Measured memory and speed of one configuration; None marks a failed run."""

    name: str
    gradient_checkpointing: bool
    sequence_length: int
    micro_batch_size: int
    accumulation_steps: int
    out_of_memory: bool
    static_allocated_gibibytes: float
    peak_allocated_gibibytes: float
    peak_reserved_gibibytes: float
    seconds_per_optimizer_step: float | None
    tokens_per_second: float | None
    trainable_parameters: int
    total_parameters: int


MEMORY_RUN_DIRECTORY = "sft/memory_runs"
MEMORY_RESULTS_PATH = f"{MEMORY_RUN_DIRECTORY}/results.jsonl"
MEMORY_REPORT_PATH = f"{MEMORY_RUN_DIRECTORY}/memory_report.md"
WARMUP_OPTIMIZER_STEPS = 2
MEASURED_OPTIMIZER_STEPS = 6
LEARNING_RATE = 1e-4
BYTES_PER_GIBIBYTE = 1024 ** 3
FULL_FINE_TUNING_BYTES_PER_PARAMETER = 16
LORA_STATE_BYTES_PER_PARAMETER = 16

MEMORY_CONFIGURATIONS: list[MemoryConfiguration] = [
    {
        "name": "checkpointing_on_len1024_batch1",
        "gradient_checkpointing": True,
        "sequence_length": 1024,
        "micro_batch_size": 1,
        "accumulation_steps": 1,
    },
    {
        "name": "checkpointing_off_len1024_batch1",
        "gradient_checkpointing": False,
        "sequence_length": 1024,
        "micro_batch_size": 1,
        "accumulation_steps": 1,
    },
    {
        "name": "checkpointing_on_len2048_batch1",
        "gradient_checkpointing": True,
        "sequence_length": 2048,
        "micro_batch_size": 1,
        "accumulation_steps": 1,
    },
    {
        "name": "checkpointing_off_len2048_batch1",
        "gradient_checkpointing": False,
        "sequence_length": 2048,
        "micro_batch_size": 1,
        "accumulation_steps": 1,
    },
    {
        "name": "checkpointing_on_len2048_batch4",
        "gradient_checkpointing": True,
        "sequence_length": 2048,
        "micro_batch_size": 4,
        "accumulation_steps": 1,
    },
    {
        "name": "checkpointing_on_len1024_batch8",
        "gradient_checkpointing": True,
        "sequence_length": 1024,
        "micro_batch_size": 8,
        "accumulation_steps": 1,
    },
    {
        "name": "checkpointing_on_len1024_batch1_accumulation8",
        "gradient_checkpointing": True,
        "sequence_length": 1024,
        "micro_batch_size": 1,
        "accumulation_steps": 8,
    },
]
