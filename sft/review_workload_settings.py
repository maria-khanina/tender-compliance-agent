"""Settings of the review-workload metric and the verdict models it compares."""
from sft.training_schemas import ModelSource

MINIMUM_PROBLEM_RECALL = 0.95
COMPLIANT_VERDICT = "compliant"
VERDICT_FIELD = '"verdict": "'
VERDICT_END = '"'
SMALL_BASE_MODEL = "Qwen/Qwen3-0.6B"
LARGE_BASE_MODEL = "Qwen/Qwen3-4B"
SMALL_QLORA_ADAPTER = (
    "sft/runs/qwen3-0.6b-lora/sft_runs/qlora_4_epochs/sft_checkpoints/final"
)
LARGE_SFT_MERGED = "sft/runs/qwen3-4b-v1/sft_runs/20260916_0404/merged"
LARGE_DPO_ADAPTER = (
    "sft/runs/qwen3-4b-v1/dpo_runs/20260916_1501_lr5e-5/dpo_checkpoints/final"
)
REVIEW_MODELS: dict[str, ModelSource] = {
    "base_0.6b": {
        "tokenizer": SMALL_BASE_MODEL,
        "weights": SMALL_BASE_MODEL,
        "adapter": None,
        "quantized": False,
    },
    "qlora_0.6b": {
        "tokenizer": SMALL_BASE_MODEL,
        "weights": SMALL_BASE_MODEL,
        "adapter": SMALL_QLORA_ADAPTER,
        "quantized": True,
    },
    "base_4b": {
        "tokenizer": LARGE_BASE_MODEL,
        "weights": LARGE_BASE_MODEL,
        "adapter": None,
        "quantized": True,
    },
    "qlora_4b": {
        "tokenizer": LARGE_BASE_MODEL,
        "weights": LARGE_SFT_MERGED,
        "adapter": None,
        "quantized": True,
    },
    "qlora_dpo_4b": {
        "tokenizer": LARGE_BASE_MODEL,
        "weights": LARGE_SFT_MERGED,
        "adapter": LARGE_DPO_ADAPTER,
        "quantized": True,
    },
}
REVIEW_SCORES_DIRECTORY = "sft/runs/review_scores"
REVIEW_REPORT = "sft/runs/review_workload_comparison.json"
RECALL_ROUNDING_DIGITS = 9
