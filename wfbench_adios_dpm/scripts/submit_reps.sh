#!/bin/bash
# submit_reps.sh — Submit chained repetitions for all benchmark configs
# Each job depends on the previous one via --dependency=afterok
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"
cd "${ROOT_DIR}"

PREV_JOB="${1:-}"  # Optional: chain after this job ID

submit_job() {
    local LABEL="$1"
    local LAUNCH_CMD="$2"

    # Run the launch script to generate the Slurm job file
    local OUTPUT
    OUTPUT=$(bash -c "${LAUNCH_CMD}" 2>&1)

    # Extract the job script path (after "sbatch ")
    local JOB_SCRIPT
    JOB_SCRIPT=$(echo "${OUTPUT}" | grep 'Submitting: sbatch' | sed 's/.*sbatch //')

    # Cancel the auto-submitted job
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

    # Submit with dependency if we have a previous job
    local SBATCH_OUT
    if [[ -n "${PREV_JOB}" ]]; then
        SBATCH_OUT=$(sbatch --dependency=afterany:${PREV_JOB} "${JOB_SCRIPT}" 2>&1)
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
    echo "  ${LABEL}: job ${JOB_ID} (dep=${PREV_JOB})"
}

for REP in 2 3; do
    echo "=== Rep ${REP} ==="
    submit_job "ssd_small_rep${REP}"       "bash scripts/run_storage.sh --size small --storage ssd --nodes 4"
    submit_job "beegfs_small_rep${REP}"    "bash scripts/run_storage.sh --size small --storage beegfs --nodes 4"
    submit_job "dpm_mixed_small_rep${REP}" "bash scripts/run_dpm_mixed.sh --size small --nodes 4"
    submit_job "adios_sst_small_rep${REP}" "bash scripts/run_adios_sst.sh --size small --nodes 4"
    submit_job "adios_sst_med_rep${REP}"   "bash scripts/run_adios_sst.sh --size medium --nodes 4"
    submit_job "adios_sst_large_rep${REP}" "bash scripts/run_adios_sst.sh --size large --nodes 4"
done

echo ""
echo "=== All jobs submitted. Last job: ${PREV_JOB} ==="
echo "Check status: squeue -u \$(whoami) --sort=i"
