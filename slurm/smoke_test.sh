#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source slurm/settings.sh
mkdir -p "${SLURM_LOG_DIR}"

gpu_check="import time, torch; print('cuda', torch.cuda.is_available(), \
torch.cuda.get_device_name(0)); time.sleep(20)"

submit_check() {
    sbatch --parsable \
        --job-name="$1" \
        --output="${SLURM_LOG_DIR}/%x-%j.log" \
        --gres=gpu:1 \
        --cpus-per-task="${CPU_JOB_CPUS}" \
        "${@:2}" \
        --wrap="${TRAINING_VENV}/bin/python -c \"${gpu_check}\""
}

first_job="$(submit_check smoke-first)"
second_job="$(submit_check smoke-second)"
third_job="$(submit_check smoke-after --dependency="afterok:${first_job}")"
sleep 3
squeue --format="%.8i %.14j %.10T %.24R"
echo "jobs: ${first_job} ${second_job} ${third_job}"
