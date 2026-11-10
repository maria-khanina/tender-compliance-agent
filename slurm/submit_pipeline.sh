#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source slurm/settings.sh

run_id="${1:-$(date +%Y%m%d_%H%M%S)}"
mkdir -p "${SLURM_LOG_DIR}"

gpu_resources="--gres=gpu:1 --cpus-per-task=${GPU_JOB_CPUS} --mem=${GPU_JOB_MEMORY}"
cpu_resources="--cpus-per-task=${CPU_JOB_CPUS} --mem=${CPU_JOB_MEMORY}"
run_variables="ALL,SFT_RUN_ID=${run_id},COMPLETED_SFT_RUN_ID=${run_id},DPO_RUN_ID=${run_id}"

submit_stage() {
    local name="$1"
    local after="$2"
    local resources="$3"
    shift 3
    local dependency=()
    if [[ -n "${after}" ]]; then
        dependency=(--dependency="afterok:${after}" --kill-on-invalid-dep=yes)
    fi
    sbatch --parsable \
        --job-name="${name}" \
        --output="${SLURM_LOG_DIR}/%x-%j.log" \
        --export="${run_variables}" \
        "${dependency[@]}" \
        ${resources} \
        slurm/run_stage.sh "$@"
}

sft_job="$(submit_stage sft "" "${gpu_resources}" sft.train_verdict_lora)"
merge_job="$(submit_stage merge "${sft_job}" "${cpu_resources}" sft.merge_sft_adapter)"
mine_job="$(submit_stage mine-pairs "${merge_job}" "${gpu_resources}" \
    sft.mine_dpo_pairs_local)"
dpo_job="$(submit_stage dpo "${mine_job}" "${gpu_resources}" sft.train_dpo)"
compare_job="$(submit_stage compare "${dpo_job}" "${gpu_resources}" \
    sft.compare_models \
    --dpo-adapter-dir "${RUN_DIR}/dpo_runs/${run_id}/dpo_checkpoints/final")"

echo "run ${run_id}: sft=${sft_job} merge=${merge_job} mine-pairs=${mine_job}"
echo "dpo=${dpo_job} compare=${compare_job}"
squeue --format="%.8i %.12j %.10T %.20R"
