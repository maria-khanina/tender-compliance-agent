#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source slurm/settings.sh
mkdir -p "${SLURM_LOG_DIR}"

run="$1"
epochs=4
single_process="ALL,MASTER_ADDR=127.0.0.1,MASTER_PORT=29511,RANK=0,LOCAL_RANK=0,WORLD_SIZE=1"
small_model="ALL,BASE_MODEL=Qwen/Qwen3-0.6B,MODEL_RUN_DIR=sft/runs/qwen3-0.6b-lora,SFT_RUN_ID=qlora_${epochs}_epochs,SFT_NUM_TRAIN_EPOCHS=${epochs}"

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

case "${run}" in
    qlora)
        submit_gpu_job qlora-equal-epochs "${small_model}" sft.train_verdict_lora
        ;;
    full)
        submit_gpu_job full-zero-offload-equal-epochs "${single_process}" \
            sft.train_full_zero --deepspeed-config sft/deepspeed_zero2_offload.json \
            --max-steps -1 --run-name "zero2_offload_${epochs}_epochs"
        ;;
esac
squeue --format="%.8i %.30j %.10T %.20R"
