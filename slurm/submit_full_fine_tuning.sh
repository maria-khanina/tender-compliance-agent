#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source slurm/settings.sh
mkdir -p "${SLURM_LOG_DIR}"

single_process="ALL,MASTER_ADDR=127.0.0.1,MASTER_PORT=29511,RANK=0,LOCAL_RANK=0,WORLD_SIZE=1"
small_model="ALL,BASE_MODEL=Qwen/Qwen3-0.6B,MODEL_RUN_DIR=sft/runs/qwen3-0.6b-lora,SFT_RUN_ID=qlora"

submit_gpu_job() {
    local name="$1"
    local variables="$2"
    shift 2
    sbatch --parsable \
        --job-name="${name}" \
        --output="${SLURM_LOG_DIR}/%x-%j.log" \
        --gres=gpu:1 \
        --cpus-per-task="${GPU_JOB_CPUS}" \
        --mem="${GPU_JOB_MEMORY}" \
        --export="${variables}" \
        slurm/run_stage.sh "$@"
}

probe_job="$(submit_gpu_job full-gpu-only-probe "${single_process}" \
    sft.train_full_zero --deepspeed-config sft/deepspeed_zero2_gpu.json \
    --max-steps 6 --run-name zero2_gpu_probe)"
offload_job="$(submit_gpu_job full-zero-offload "${single_process}" \
    sft.train_full_zero --deepspeed-config sft/deepspeed_zero2_offload.json \
    --max-steps -1 --run-name zero2_offload)"
lora_job="$(submit_gpu_job small-qlora "${small_model}" sft.train_verdict_lora)"

echo "gpu-only probe=${probe_job} zero-offload=${offload_job} qlora=${lora_job}"
squeue --format="%.8i %.22j %.10T %.20R"
