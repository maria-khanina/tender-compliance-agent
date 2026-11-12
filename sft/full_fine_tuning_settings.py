"""Settings of full fine-tuning of the small verdict model with DeepSpeed ZeRO."""

FULL_MODEL = "Qwen/Qwen3-0.6B"
FULL_RUN_DIRECTORY = "sft/runs/qwen3-0.6b-full"
OFFLOAD_CONFIG_PATH = "sft/deepspeed_zero2_offload.json"
GPU_ONLY_CONFIG_PATH = "sft/deepspeed_zero2_gpu.json"
LEARNING_RATE = 1e-5
WEIGHT_DECAY = 0.01
EPOCHS = 4
MAXIMUM_SEQUENCE_LENGTH = 2304
MICRO_BATCH_SIZE = 1
ACCUMULATION_STEPS = 8
EVALUATE_EVERY_STEPS = 40
EARLY_STOP_PATIENCE = 3
EARLY_STOP_MINIMUM_DELTA = 0.01
LOGGING_STEPS = 10
WARMUP_OPTIMIZER_STEPS = 2
BYTES_PER_GIBIBYTE = 1024 ** 3
QLORA_EQUAL_EPOCHS_HISTORY = (
    "sft/runs/qwen3-0.6b-lora/sft_runs/qlora_4_epochs/sft_training_history.json"
)
FULL_EQUAL_EPOCHS_HISTORY = (
    "sft/runs/qwen3-0.6b-full/zero2_offload_4_epochs/validation_history.json"
)
EQUAL_EPOCHS_REPORT = "sft/runs/equal_epoch_comparison.json"
BOOTSTRAP_RESAMPLES = 10000
BOOTSTRAP_SEED = 0
CONFIDENCE_LEVEL = 0.95
PERCENT = 100
