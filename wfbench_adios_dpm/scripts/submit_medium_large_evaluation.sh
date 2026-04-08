#!/bin/bash
# submit_medium_large_evaluation.sh — Medium/large benchmarks with trial ordering
#
# Order (single sbatch dependency chain):
#   1. File-based trial 1: medium (SSD → BeeGFS → DPM) + large (SSD → BeeGFS → DPM)
#   2. File-based trial 2: same six jobs
#   3. File-based trial 3: same six jobs
#   4. ADIOS SST trial 2: medium, large
#   5. ADIOS SST trial 3: medium, large
#
# Trial 1 for ADIOS medium/large is assumed done separately (initial scaling study);
# this script runs repetitions 2–3 for ADIOS only.
#
# Usage:
#   ./run_chain.sh [PREV_JOB_ID]          # from wfbench_adios_dpm/ (checks config.env)
#   bash scripts/submit_medium_large_evaluation.sh [PREV_JOB_ID]
#
# If PREV_JOB_ID is set, the first job waits for that job (afterok). NODES via env (default 4).
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"
cd "${ROOT_DIR}"

PREV_JOB="${1:-}"
NODES="${NODES:-4}"

submit_job() {
    local LABEL="$1"
    local LAUNCH_CMD="$2"

    local OUTPUT
    OUTPUT=$(bash -c "${LAUNCH_CMD}" 2>&1)

    local JOB_SCRIPT
    JOB_SCRIPT=$(echo "${OUTPUT}" | grep 'Submitting: sbatch' | sed 's/.*sbatch //')

    local AUTO_JOB
    AUTO_JOB=$(echo "${OUTPUT}" | grep 'Submitted batch job' | awk '{print $NF}')
    if [[ -n "${AUTO_JOB}" ]]; then
        scancel "${AUTO_JOB}" 2>/dev/null || true
    fi

    if [[ -z "${JOB_SCRIPT}" ]]; then
        echo "ERROR: could not extract job script for ${LABEL}"
        echo "Output was: ${OUTPUT}"
        return 1
    fi

    local SBATCH_OUT
    if [[ -n "${PREV_JOB}" ]]; then
        SBATCH_OUT=$(sbatch --dependency=afterany:"${PREV_JOB}" "${JOB_SCRIPT}" 2>&1)
    else
        SBATCH_OUT=$(sbatch "${JOB_SCRIPT}" 2>&1)
    fi

    local JOB_ID
    JOB_ID=$(echo "${SBATCH_OUT}" | grep 'Submitted batch job' | awk '{print $NF}')

    if [[ -z "${JOB_ID}" ]]; then
        echo "ERROR: sbatch failed for ${LABEL}: ${SBATCH_OUT}"
        return 1
    fi

    PREV_JOB="${JOB_ID}"
    echo "  ${LABEL}: job ${JOB_ID}"
}

echo "=== Medium/large evaluation (${NODES} nodes) ==="
if [[ -n "${PREV_JOB:-}" ]]; then
    echo "    Chain starts after: afterok:${PREV_JOB}"
fi

for TRIAL in 1 2 3; do
    echo ""
    echo "--- File-based trial ${TRIAL}/3 (medium + large) ---"
    submit_job "t${TRIAL}_ssd_medium"       "bash scripts/run_storage.sh --size medium --storage ssd --nodes ${NODES}"
    submit_job "t${TRIAL}_beegfs_medium"    "bash scripts/run_storage.sh --size medium --storage beegfs --nodes ${NODES}"
    submit_job "t${TRIAL}_dpm_mixed_medium" "bash scripts/run_dpm_mixed.sh --size medium --nodes ${NODES}"
    submit_job "t${TRIAL}_ssd_large"        "bash scripts/run_storage.sh --size large --storage ssd --nodes ${NODES}"
    submit_job "t${TRIAL}_beegfs_large"     "bash scripts/run_storage.sh --size large --storage beegfs --nodes ${NODES}"
    submit_job "t${TRIAL}_dpm_mixed_large"  "bash scripts/run_dpm_mixed.sh --size large --nodes ${NODES}"
done

for ADIOS_TRIAL in 2 3; do
    echo ""
    echo "--- ADIOS SST trial ${ADIOS_TRIAL}/3 (medium + large only) ---"
    submit_job "adios_t${ADIOS_TRIAL}_medium" "bash scripts/run_adios_sst.sh --size medium --nodes ${NODES}"
    submit_job "adios_t${ADIOS_TRIAL}_large"  "bash scripts/run_adios_sst.sh --size large --nodes ${NODES}"
done

echo ""
echo "=== Done. Last job ID: ${PREV_JOB} ==="
echo "Monitor: squeue -u \$(whoami) --sort=i"
