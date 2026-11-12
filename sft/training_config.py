"""Centralized paths and hyperparameters for the SFT/DPO training pipeline."""
import datetime
import os

BASE_MODEL = os.environ.get("BASE_MODEL", "Qwen/Qwen3-4B")
RUN_DIR = os.environ.get("MODEL_RUN_DIR", "sft/runs/qwen3-4b-v1")
DATA_DIR = "sft/data"
TRAIN_DATA_PATH = f"{DATA_DIR}/sft_train_dataset.jsonl"
VAL_DATA_PATH = f"{DATA_DIR}/sft_validation_dataset.jsonl"
SFT_DATASET_COLLECTION_PREFIX = "sft_"

SFT_RUN_ID = (
    os.environ.get("SFT_RUN_ID") or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
)
SFT_RUN_DIR = f"{RUN_DIR}/sft_runs/{SFT_RUN_ID}"

COMPLETED_SFT_RUN_ID = os.environ.get("COMPLETED_SFT_RUN_ID", "20260916_0404")
COMPLETED_SFT_RUN_DIR = f"{RUN_DIR}/sft_runs/{COMPLETED_SFT_RUN_ID}"
MERGED_MODEL_DIR = f"{COMPLETED_SFT_RUN_DIR}/merged"
DPO_TRAIN_DATA_PATH = f"{COMPLETED_SFT_RUN_DIR}/dpo_train_dataset.jsonl"

DPO_RUN_ID = (
    os.environ.get("DPO_RUN_ID") or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
)
DPO_RUN_DIR = f"{RUN_DIR}/dpo_runs/{DPO_RUN_ID}"

LORA_RANK = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.1
LORA_TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]

EVAL_MAX_NEW_TOKENS = 512

SFT_MAX_SEQ_LEN = 2304
SFT_PER_DEVICE_TRAIN_BATCH_SIZE = 1
SFT_GRADIENT_ACCUMULATION_STEPS = 8
SFT_LEARNING_RATE = 1e-4
SFT_WEIGHT_DECAY = 0.01
SFT_NUM_TRAIN_EPOCHS = int(os.environ.get("SFT_NUM_TRAIN_EPOCHS", "6"))
SFT_LOGGING_STEPS = 10
SFT_EARLY_STOP_PATIENCE = 3
SFT_EARLY_STOP_MIN_DELTA = 0.01
SFT_EVAL_EVERY_N_STEPS = 40
SFT_SAVE_EVERY_N_STEPS = 15

DPO_MAX_SEQ_LEN = 1984  # actual max in the mined dataset is 1935, so this is a
# no-loss safety margin, not a real truncation -- lowered from 2304 after
# a real OOM at step 4/13 (fragmentation: 3.97GiB reserved-but-unallocated
# vs a 2.45GiB request), same lever as the earlier Qwen3-8B run used.
DPO_BETA = 0.1
DPO_PER_DEVICE_TRAIN_BATCH_SIZE = 1
DPO_GRADIENT_ACCUMULATION_STEPS = 8
DPO_NUM_TRAIN_EPOCHS = 1
DPO_LEARNING_RATE = 5e-5  # was 5e-6 -- a run at that rate showed
# rewards/margins ~0 and byte-identical macro_f1 across 3 separate evals,
# meaning the LoRA weights weren't moving enough in 13 steps to change even
# one greedy prediction. Raised 10x to be in the same range as the SFT
# stage's LoRA learning rate, standard practice for LoRA DPO with only
# ~13 gradient steps available.
DPO_WEIGHT_DECAY = 0.01
DPO_LOGGING_STEPS = 1
DPO_EVAL_EVERY_N_STEPS = 3  # only 13 total steps this run -- 5-8 step cadence
# left the run with zero visible loss/eval before every prior crash at
# step 3-4; smaller cadence trades some eval overhead for actually
# seeing progress on a run this short.

MINING_SAMPLES_PER_PROMPT = 8
MINING_MAX_NEW_TOKENS = 300
MINING_TEMPERATURE = 0.8

DEFAULT_SFT_ADAPTER_DIR = f"{COMPLETED_SFT_RUN_DIR}/sft_checkpoints/final"
DEFAULT_DPO_ADAPTER_DIR = (
    f"{RUN_DIR}/dpo_runs/20260916_1501_lr5e-5/dpo_checkpoints/final"
)
