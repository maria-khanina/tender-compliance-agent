"""Train the QLoRA verdict adapter on all folds but one and score the held-out fold.

The adapter is trained with the SFT settings of sft/training_config.py for a
fixed FOLD_EPOCHS epochs, without evaluations during training and without
choosing a step, so the held-out tender influences nothing but its own
scores. After training the probabilities of every verdict of the held-out
cases are written to sft/runs/review_scores/folds/qlora_0.6b/fold_<k>.json.
The base model comes from BASE_MODEL (Qwen/Qwen3-0.6B in the Slurm job).

Usage (from the repository root, on the GPU):
  BASE_MODEL=Qwen/Qwen3-0.6B python -m sft.train_fold_qlora --fold 0
"""
import argparse

from datasets import Dataset
from transformers import PreTrainedTokenizerBase
from trl import SFTConfig, SFTTrainer  # type: ignore[reportPrivateImportUsage]

from sft.fold_settings import (
    FOLD_EPOCHS,
    FOLD_RUN_DIRECTORY,
    FOLD_SCORES_DIRECTORY,
    TRAINED_FOLD_MODEL,
)
from sft.folds import split_fold
from sft.peft_utils import as_peft_model
from sft.score_review_models import save_scores, score_rows
from sft.train_verdict_lora import load_model_and_tokenizer
from sft.training_config import (
    SFT_GRADIENT_ACCUMULATION_STEPS,
    SFT_LEARNING_RATE,
    SFT_LOGGING_STEPS,
    SFT_MAX_SEQ_LEN as SFT_MAXIMUM_SEQUENCE_LENGTH,
    SFT_PER_DEVICE_TRAIN_BATCH_SIZE,
    SFT_WEIGHT_DECAY,
)
from sft.training_schemas import ChatExample


def parse_arguments() -> argparse.Namespace:
    """Read which fold to hold out."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--fold", type=int, required=True)
    return parser.parse_args()


def build_config(run_directory: str) -> SFTConfig:
    """Describe the fixed-length QLoRA training run of one fold."""
    return SFTConfig(
        output_dir=run_directory,
        per_device_train_batch_size=SFT_PER_DEVICE_TRAIN_BATCH_SIZE,
        gradient_accumulation_steps=SFT_GRADIENT_ACCUMULATION_STEPS,
        gradient_checkpointing=True,
        learning_rate=SFT_LEARNING_RATE,
        weight_decay=SFT_WEIGHT_DECAY,
        num_train_epochs=FOLD_EPOCHS,
        logging_steps=SFT_LOGGING_STEPS,
        save_strategy="no",
        max_length=SFT_MAXIMUM_SEQUENCE_LENGTH,
        bf16=True,
        report_to=[],
        assistant_only_loss=True,
    )


def train_adapter(
    training_rows: list[ChatExample],
    run_directory: str,
) -> tuple[SFTTrainer, PreTrainedTokenizerBase]:
    """Train the adapter on the training cases and save it."""
    model, tokenizer = load_model_and_tokenizer()
    dataset = Dataset.from_list(training_rows)  # type: ignore[reportArgumentType]
    trainer = SFTTrainer(
        model=model,
        args=build_config(run_directory),
        train_dataset=dataset,
        processing_class=tokenizer,
    )
    trainer.train()
    as_peft_model(trainer.model).save_pretrained(f"{run_directory}/adapter")
    return trainer, tokenizer


def main() -> None:
    """Train on the other folds and score the held-out one."""
    arguments = parse_arguments()
    training_rows, held_out_rows = split_fold(arguments.fold)
    print(f"fold {arguments.fold}: {len(training_rows)} training, "
          f"{len(held_out_rows)} held-out cases")
    run_directory = f"{FOLD_RUN_DIRECTORY}/fold_{arguments.fold}"
    trainer, tokenizer = train_adapter(training_rows, run_directory)
    scored = score_rows(as_peft_model(trainer.model), tokenizer, held_out_rows)
    path = f"{FOLD_SCORES_DIRECTORY}/{TRAINED_FOLD_MODEL}/fold_{arguments.fold}.json"
    save_scores(scored, path)


if __name__ == "__main__":
    main()
