"""Settings of the tender-grouped K-fold comparison of the verdict models."""

FOLD_COUNT = 5
FOLDS_PATH = "sft/folds.json"
FOLD_EPOCHS = 4
FOLD_RUN_DIRECTORY = "sft/runs/qwen3-0.6b-lora/folds"
FOLD_SCORES_DIRECTORY = "sft/runs/review_scores/folds"
FOLD_REPORT = "sft/runs/review_workload_folds.json"
FOLD_MODELS = ("base_0.6b", "qlora_0.6b", "base_4b")
TRAINED_FOLD_MODEL = "qlora_0.6b"
