"""Render the memory and step-time measurements as a Markdown report.

Usage:
  python -m sft.memory_report
"""
import json

from sft.memory_experiment_settings import (
    BYTES_PER_GIBIBYTE,
    FULL_FINE_TUNING_BYTES_PER_PARAMETER,
    LORA_STATE_BYTES_PER_PARAMETER,
    MEMORY_CONFIGURATIONS,
    MEMORY_REPORT_PATH,
    MEMORY_RESULTS_PATH,
    MemoryResult,
)

TABLE_HEADER = (
    "| Configuration | Checkpointing | Tokens per micro-batch | Micro-batches per "
    "step | Static GiB | Peak allocated GiB | Peak reserved GiB | Seconds per "
    "step | Tokens per second |\n"
    "|---|---|---|---|---|---|---|---|---|"
)


def load_latest_results() -> list[MemoryResult]:
    """Return the newest result of every configuration, in configuration order."""
    latest: dict[str, MemoryResult] = {}
    with open(MEMORY_RESULTS_PATH, encoding="utf-8") as results_file:
        for line in results_file:
            result: MemoryResult = json.loads(line)
            latest[result["name"]] = result
    names: list[str] = [
        configuration["name"] for configuration in MEMORY_CONFIGURATIONS
    ]
    return [latest[name] for name in names if name in latest]


def format_optional(value: float | None) -> str:
    """Format a measured value, or say that the run ran out of memory."""
    if value is None:
        return "out of memory"
    return f"{value:.2f}"


def render_row(result: MemoryResult) -> str:
    """Render one configuration as a table row."""
    tokens = result["micro_batch_size"] * result["sequence_length"]
    checkpointing = "on" if result["gradient_checkpointing"] else "off"
    cells: list[str] = [
        result["name"],
        checkpointing,
        str(tokens),
        str(result["accumulation_steps"]),
        f"{result['static_allocated_gibibytes']:.2f}",
        f"{result['peak_allocated_gibibytes']:.2f}",
        f"{result['peak_reserved_gibibytes']:.2f}",
        format_optional(result["seconds_per_optimizer_step"]),
        format_optional(result["tokens_per_second"]),
    ]
    return "| " + " | ".join(cells) + " |"


def render_estimates(result: MemoryResult) -> str:
    """Compare the measured static memory with full fine-tuning estimates."""
    full_bytes = result["total_parameters"] * FULL_FINE_TUNING_BYTES_PER_PARAMETER
    lora_bytes = result["trainable_parameters"] * LORA_STATE_BYTES_PER_PARAMETER
    return (
        f"- Parameters: {result['total_parameters']:,} in total, "
        f"{result['trainable_parameters']:,} trainable (LoRA).\n"
        f"- Full fine-tuning with Adam in mixed precision needs about "
        f"{FULL_FINE_TUNING_BYTES_PER_PARAMETER} bytes per parameter (bf16 weights "
        f"and gradients, fp32 master weights, two fp32 Adam moments): "
        f"{full_bytes / BYTES_PER_GIBIBYTE:.1f} GiB before activations.\n"
        f"- LoRA weights, gradients and Adam moments take "
        f"{lora_bytes / BYTES_PER_GIBIBYTE:.2f} GiB; the frozen 4-bit base and "
        f"the adapter together measured {result['static_allocated_gibibytes']:.2f} "
        f"GiB before the first step."
    )


def render_report(results: list[MemoryResult]) -> str:
    """Render the whole Markdown report."""
    rows: list[str] = [render_row(result) for result in results]
    return (
        "# Training memory and step time\n\n"
        + TABLE_HEADER
        + "\n"
        + "\n".join(rows)
        + "\n\n## Memory budget\n\n"
        + render_estimates(results[0])
        + "\n"
    )


def main() -> None:
    """Write the report next to the results file."""
    report = render_report(load_latest_results())
    with open(MEMORY_REPORT_PATH, "w", encoding="utf-8") as report_file:
        report_file.write(report)
    print(report)


if __name__ == "__main__":
    main()
