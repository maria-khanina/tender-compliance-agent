#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source slurm/settings.sh
mkdir -p "${SLURM_LOG_DIR}"

for model in "$@"; do
    sbatch --parsable \
        --job-name="review-scores-${model}" \
        --output="${SLURM_LOG_DIR}/%x-%j.log" \
        --gres=gpu:1 \
        --cpus-per-task="${GPU_JOB_CPUS}" \
        --mem="${GPU_JOB_MEMORY}" \
        --export=ALL \
        slurm/run_stage.sh sft.score_review_models --model "${model}"
done
squeue --format="%.8i %.30j %.10T %.20R"
