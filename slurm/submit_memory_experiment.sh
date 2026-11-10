#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source slurm/settings.sh
mkdir -p "${SLURM_LOG_DIR}"

configurations="$("${TRAINING_VENV}/bin/python" -c \
    "from sft.memory_experiment_settings import MEMORY_CONFIGURATIONS; \
print(' '.join(entry['name'] for entry in MEMORY_CONFIGURATIONS))")"

measurement_jobs=()
for configuration in ${configurations}; do
    measurement_jobs+=("$(sbatch --parsable \
        --job-name="memory-${configuration}" \
        --output="${SLURM_LOG_DIR}/%x-%j.log" \
        --gres=gpu:1 \
        --cpus-per-task="${GPU_JOB_CPUS}" \
        --mem="${GPU_JOB_MEMORY}" \
        slurm/run_stage.sh sft.memory_experiment --configuration "${configuration}")")
done

dependency="afterany:$(IFS=:; echo "${measurement_jobs[*]}")"
report_job="$(sbatch --parsable \
    --job-name=memory-report \
    --output="${SLURM_LOG_DIR}/%x-%j.log" \
    --dependency="${dependency}" \
    --cpus-per-task=1 \
    slurm/run_stage.sh sft.memory_report)"

echo "measurements: ${measurement_jobs[*]} report: ${report_job}"
squeue --format="%.8i %.48j %.10T %.20R"
