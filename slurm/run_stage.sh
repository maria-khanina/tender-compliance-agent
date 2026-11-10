#!/usr/bin/env bash
set -euo pipefail

cd "${SLURM_SUBMIT_DIR}"
source slurm/settings.sh
source "${TRAINING_VENV}/bin/activate"

echo "job=${SLURM_JOB_ID} name=${SLURM_JOB_NAME} run=${SFT_RUN_ID}"
echo "gpus=${CUDA_VISIBLE_DEVICES:-none} start=$(date --iso-8601=seconds)"
python -m "$@"
echo "end=$(date --iso-8601=seconds)"
