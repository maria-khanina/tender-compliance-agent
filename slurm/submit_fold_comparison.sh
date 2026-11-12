#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source slurm/settings.sh
mkdir -p "${SLURM_LOG_DIR}"

small_model="ALL,BASE_MODEL=Qwen/Qwen3-0.6B"

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

for model in base_0.6b base_4b; do
    submit_gpu_job "fold-scores-${model}" ALL sft.score_fold_models --model "${model}"
done
for fold in 0 1 2 3 4; do
    submit_gpu_job "fold-qlora-${fold}" "${small_model}" sft.train_fold_qlora --fold "${fold}"
done
squeue --format="%.8i %.30j %.10T %.20R"
