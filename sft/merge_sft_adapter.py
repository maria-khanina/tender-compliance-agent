"""Merge the trained verdict-generation SFT LoRA adapter into the base
model, once, producing a plain (non-PEFT) checkpoint on disk. This
merged checkpoint becomes the frozen "reference" model for the DPO
stage: train_dpo.py loads it as its base and attaches a NEW LoRA
adapter on top, so DPO can be turned on/off by swapping just that new
adapter, independent of the SFT weights it started from.

Merges shard-by-shard directly against the safetensors files, not via
peft's merge_and_unload() on a fully materialized model -- that needs the
whole bf16 base resident in memory at once (merging is floating-point
addition into the weights -- peft can't do it on a 4-bit-quantized base
in place), and separately, whole-model device_map="auto" offloading hit
a peft/accelerate version-compat bug on this machine (KeyError in
_update_offload) when this script targeted Qwen3-8B. Streaming
shard-by-shard (each shard a few GB) sidesteps both: only ever one
shard's tensors resident at a time, plus the LoRA adapter itself (tens
of MB). Kept for the Qwen3-4B model too even though its smaller size
makes the whole-model approach more plausible -- no reason to
reintroduce either failure mode.

The resulting merged checkpoint stays in bf16 on disk -- it is
re-quantized to 4-bit when train_dpo.py loads it for actual training,
matching the SFT script's own precision, same as the original
whole-model approach was documented to do.

Runs in the WSL venv at /root/sft/venv, same as train_verdict_lora.py.

Usage:
  python sft/merge_sft_adapter.py \
      --adapter-dir sft/runs/qwen3-4b-v1/sft_runs/<run-id>/sft_checkpoints/final \
      --output-dir sft/runs/qwen3-4b-v1/sft_runs/<run-id>/merged
"""
import argparse
import json
import os
import pathlib
import shutil

import torch
from huggingface_hub import snapshot_download
from safetensors import safe_open
from safetensors.torch import save_file

from sft.training_config import BASE_MODEL, DEFAULT_SFT_ADAPTER_DIR

# Non-weight files a HF model directory needs alongside the safetensors
# shards for AutoModelForCausalLM/AutoTokenizer.from_pretrained to work.
BASE_FILES_TO_COPY = ["config.json", "generation_config.json"]


LoraDeltas = dict[str, tuple[torch.Tensor, torch.Tensor]]


def load_lora_deltas(adapter_dir: str) -> tuple[LoraDeltas, float]:
    """Returns {base_weight_key: (lora_A, lora_B)} and the scaling factor
    (lora_alpha / r), reading the adapter's own config rather than
    assuming train_verdict_lora.py's current values -- this must stay
    correct even if that script's LoraConfig changes later."""
    adapter_config_path = f"{adapter_dir}/adapter_config.json"
    adapter_config = json.load(open(adapter_config_path, encoding="utf-8"))
    if adapter_config.get("use_dora") or adapter_config.get("use_rslora"):
        raise NotImplementedError(
            "adapter uses DoRA/rsLoRA -- this script's merge formula "
            "(base + (B @ A) * alpha/r) only covers plain LoRA"
        )
    scaling = adapter_config["lora_alpha"] / adapter_config["r"]

    pairs: dict[str, dict[str, torch.Tensor]] = {}
    with safe_open(f"{adapter_dir}/adapter_model.safetensors", framework="pt") as f:
        for key in f.keys():
            # e.g. "base_model.model.model.layers.0.mlp.down_proj.lora_A.weight"
            # -> base weight key "model.layers.0.mlp.down_proj.weight"
            assert key.startswith("base_model.model.")
            assert key.endswith(".weight")
            for suffix in (".lora_A.weight", ".lora_B.weight"):
                if key.endswith(suffix):
                    base_key = key[len("base_model.model."):-len(suffix)] + ".weight"
                    which = "A" if suffix == ".lora_A.weight" else "B"
                    pairs.setdefault(base_key, {})[which] = f.get_tensor(key)
                    break

    deltas: LoraDeltas = {}
    for base_key, ab in pairs.items():
        assert "A" in ab and "B" in ab, f"incomplete LoRA pair for {base_key}"
        deltas[base_key] = (ab["A"], ab["B"])
    return deltas, scaling


def group_tensor_names_by_shard(weight_map: dict[str, str]) -> dict[str, list[str]]:
    by_shard: dict[str, list[str]] = {}
    for tensor_name, shard_file in weight_map.items():
        by_shard.setdefault(shard_file, []).append(tensor_name)
    return by_shard


def merge_shard(
    base_dir: str,
    shard_file: str,
    tensor_names: list[str],
    deltas: LoraDeltas,
    scaling: float,
    output_dir: str,
) -> set[str]:
    applied: set[str] = set()
    out_tensors: dict[str, torch.Tensor] = {}
    with safe_open(f"{base_dir}/{shard_file}", framework="pt") as f:
        for name in tensor_names:
            tensor = f.get_tensor(name)
            if name in deltas:
                lora_A, lora_B = deltas[name]
                # Exactly peft's own get_delta_weight() + merge():
                # compute B @ A * scaling in float32 (matches peft's
                # "cast to fp32 on CPU to avoid slow bf16 matmul"
                # path), round that delta back down to the base
                # tensor's own dtype, *then* add -- in bf16, not
                # float32. Rounding before the add (not after) is
                # what peft actually does; matching it exactly avoids
                # a last-bit numerical mismatch from a merge done
                # this way instead of through peft's own code path.
                delta = ((lora_B.float() @ lora_A.float()) * scaling).to(tensor.dtype)
                tensor = tensor + delta
                applied.add(name)
            out_tensors[name] = tensor.contiguous()
    save_file(out_tensors, f"{output_dir}/{shard_file}", metadata={"format": "pt"})
    return applied


def merge_all_shards(
    base_dir: str, weight_map: dict[str, str], deltas: LoraDeltas, scaling: float,
    output_dir: str,
) -> set[str]:
    applied: set[str] = set()
    by_shard = group_tensor_names_by_shard(weight_map)
    for shard_file, tensor_names in sorted(by_shard.items()):
        print(f"Processing {shard_file} ({len(tensor_names)} tensors)...")
        applied |= merge_shard(
            base_dir, shard_file, tensor_names, deltas, scaling, output_dir
        )
    return applied


def copy_non_weight_files(base_dir: str, adapter_dir: str, output_dir: str) -> None:
    from transformers import AutoTokenizer

    index_path = "model.safetensors.index.json"
    shutil.copy(f"{base_dir}/{index_path}", f"{output_dir}/{index_path}")
    for fname in BASE_FILES_TO_COPY:
        src = f"{base_dir}/{fname}"
        if os.path.exists(src):
            shutil.copy(src, f"{output_dir}/{fname}")

    tokenizer = AutoTokenizer.from_pretrained(adapter_dir)
    tokenizer.save_pretrained(output_dir)


def merge_and_save(base_model_name: str, adapter_dir: str, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)

    print(f"Resolving local snapshot for {base_model_name}...")
    base_dir = snapshot_download(base_model_name)

    print("Loading LoRA deltas...")
    deltas, scaling = load_lora_deltas(adapter_dir)
    print(f"{len(deltas)} LoRA-targeted tensors, scaling={scaling}")

    index_path = f"{base_dir}/model.safetensors.index.json"
    index = json.load(open(index_path, encoding="utf-8"))
    weight_map: dict[str, str] = index["weight_map"]

    applied = merge_all_shards(base_dir, weight_map, deltas, scaling, output_dir)
    missing = set(deltas) - applied
    assert not missing, f"LoRA deltas never applied (base tensor not found): {missing}"
    print(f"Applied {len(applied)}/{len(deltas)} LoRA deltas across all shards")

    copy_non_weight_files(base_dir, adapter_dir, output_dir)
    print(f"Merged model saved to {output_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", default=BASE_MODEL)
    parser.add_argument("--adapter-dir", default=DEFAULT_SFT_ADAPTER_DIR)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()
    output_dir = args.output_dir or str(
        pathlib.Path(args.adapter_dir).parent.parent / "merged"
    )
    merge_and_save(args.base_model, args.adapter_dir, output_dir)


if __name__ == "__main__":
    main()
