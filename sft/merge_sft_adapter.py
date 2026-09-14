"""Merge the trained verdict-generation SFT LoRA adapter into the base
model, once, producing a plain (non-PEFT) checkpoint on disk. This
merged checkpoint becomes the frozen "reference" model for the DPO
stage: train_dpo.py loads it as its base and attaches a NEW LoRA
adapter on top, so DPO can be turned on/off by swapping just that new
adapter, independent of the SFT weights it started from.

peft's merge_and_unload() needs floating-point weights -- it cannot
merge into a 4-bit bitsandbytes-quantized base in place, so this script
loads the base in bf16 (not 4-bit) purely for this one-off merge; the
resulting merged checkpoint is re-quantized to 4-bit when train_dpo.py
loads it for actual training, matching the SFT script's own precision.

Runs in the WSL venv at /root/sft/venv, same as train_verdict_lora.py.

Usage:
  python sft/merge_sft_adapter.py \
      --adapter-dir sft/checkpoints/verdict-lora/final \
      --output-dir sft/checkpoints/verdict-lora-merged
"""
import argparse

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE_MODEL = "Qwen/Qwen3-8B"


def merge_and_save(base_model_name: str, adapter_dir: str, output_dir: str) -> None:
    tokenizer = AutoTokenizer.from_pretrained(adapter_dir)
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name, torch_dtype=torch.bfloat16
    )
    peft_model = PeftModel.from_pretrained(base_model, adapter_dir)
    merged_model = peft_model.merge_and_unload()
    merged_model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Merged model saved to {output_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", default=BASE_MODEL)
    parser.add_argument(
        "--adapter-dir", default="sft/checkpoints/verdict-lora/final"
    )
    parser.add_argument(
        "--output-dir", default="sft/checkpoints/verdict-lora-merged"
    )
    args = parser.parse_args()
    merge_and_save(args.base_model, args.adapter_dir, args.output_dir)


if __name__ == "__main__":
    main()
