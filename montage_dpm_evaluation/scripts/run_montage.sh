#!/bin/bash
# run_montage.sh — Run Montage pipeline on specified storage and node count
#
# Executes the full 10-stage Montage mosaicking pipeline with per-stage timing,
# writing intermediate data to the selected storage backend. Designed to match
# the DPM evaluation pattern used for 1000 Genomes, PyflexTRKR, and DeepDriveMD.
#
# Usage:
#   bash scripts/run_montage.sh --size large --storage ssd    --nodes 4
#   bash scripts/run_montage.sh --size large --storage beegfs --nodes 8
#   bash scripts/run_montage.sh --size large --storage tmpfs  --nodes 16

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"
source "${ROOT_DIR}/config.env"

# ── Parse arguments ───────────────────────────────────────────────────────────
SIZE="large"
STORAGE="ssd"
NODES="${NODES:-4}"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --size)    SIZE="$2";    shift 2 ;;
        --storage) STORAGE="$2"; shift 2 ;;
        --nodes)   NODES="$2";   shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

# Map storage name to path
case "${STORAGE}" in
    ssd)    STORAGE_PATH="${LOCAL_SSD_PATH}" ;;
    beegfs) STORAGE_PATH="${BEEGFS_PATH}"    ;;
    tmpfs)  STORAGE_PATH="${TMPFS_PATH}"     ;;
    *)      echo "Unknown storage: ${STORAGE}"; exit 1 ;;
esac

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUN_ID="${STORAGE}_${SIZE}_${NODES}n_${TIMESTAMP}"
RESULTS_DIR="${ROOT_DIR}/results/${RUN_ID}"
mkdir -p "${RESULTS_DIR}"

# Input data
DATA_DIR="${ROOT_DIR}/data/${SIZE}"
RAW_DIR="${DATA_DIR}/raw_images"
HDR_FILE="${DATA_DIR}/region.hdr"

if [[ ! -f "${HDR_FILE}" ]]; then
    echo "ERROR: region.hdr not found at ${HDR_FILE}"
    echo "Run: bash scripts/download_data.sh --size ${SIZE}"
    exit 1
fi

FITS_COUNT=$(ls "${RAW_DIR}"/*.fits 2>/dev/null | wc -l)
if [[ "${FITS_COUNT}" -eq 0 ]]; then
    echo "ERROR: No FITS files in ${RAW_DIR}"
    exit 1
fi

echo "=== Montage DPM Evaluation ==="
echo "    Size: ${SIZE} (${FITS_COUNT} FITS images)"
echo "    Storage: ${STORAGE} (${STORAGE_PATH})"
echo "    Nodes: ${NODES}"
echo "    Results: ${RESULTS_DIR}"

# ── Write Slurm job script ────────────────────────────────────────────────────
JOB_SCRIPT="${RESULTS_DIR}/job_montage.sh"
cat > "${JOB_SCRIPT}" << 'SLURM_HEADER'
#!/bin/bash
SLURM_HEADER

cat >> "${JOB_SCRIPT}" << SLURM_DIRECTIVES
#SBATCH --job-name=montage_${STORAGE}_${NODES}n
#SBATCH --partition=${PARTITION}
#SBATCH --account=${ACCOUNT}
#SBATCH --nodes=${NODES}
#SBATCH --ntasks-per-node=${CORES_PER_NODE}
#SBATCH --time=04:00:00
#SBATCH --output=${RESULTS_DIR}/slurm_%j.out
#SBATCH --error=${RESULTS_DIR}/slurm_%j.err
SLURM_DIRECTIVES

cat >> "${JOB_SCRIPT}" << SLURM_BODY

set -euo pipefail

source ${ROOT_DIR}/config.env
export PATH="${MONTAGE_BIN}:\${PATH}"

# Optional Darshan tracing
if [[ -n "${DARSHAN_LIB}" ]] && [[ -f "${DARSHAN_LIB}" ]]; then
    export LD_PRELOAD="${DARSHAN_LIB}"
    export DARSHAN_LOG_DIR="${RESULTS_DIR}/darshan_logs"
    mkdir -p "\${DARSHAN_LOG_DIR}"
    echo "[montage] Darshan tracing enabled"
fi

# Working directories on target storage
WORK_DIR="${STORAGE_PATH}/montage_eval_\${SLURM_JOB_ID}"
PROJ_DIR="\${WORK_DIR}/projected"
DIFF_DIR="\${WORK_DIR}/diffs"
CORR_DIR="\${WORK_DIR}/corrected"
mkdir -p "\${PROJ_DIR}" "\${DIFF_DIR}" "\${CORR_DIR}"

cleanup() {
    echo "[cleanup] removing \${WORK_DIR}"
    rm -rf "\${WORK_DIR}"
}
trap cleanup EXIT INT TERM

echo "=== Montage Pipeline: storage=${STORAGE}, nodes=${NODES} ==="
echo "Work dir: \${WORK_DIR}"
echo "Start: \$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# ── Stage 1: mImgtbl (metadata extraction) ─────────────────────────────────
echo ""
echo "--- Stage 1: mImgtbl ---"
T1_START=\$(date +%s)
mImgtbl "${RAW_DIR}" "\${WORK_DIR}/images.tbl"
T1_END=\$(date +%s)
T1=\$((T1_END - T1_START))
echo "mImgtbl time: \${T1}s"

# ── Stage 2: mProjExec (reprojection — parallel per image) ────────────────
echo ""
echo "--- Stage 2: mProjExec ---"
T2_START=\$(date +%s)
mProjExec -p "${RAW_DIR}" "\${WORK_DIR}/images.tbl" "${HDR_FILE}" "\${PROJ_DIR}" "\${WORK_DIR}/stats.tbl"
T2_END=\$(date +%s)
T2=\$((T2_END - T2_START))
echo "mProjExec time: \${T2}s"

# ── Stage 3: mImgtbl (projected catalog) ───────────────────────────────────
echo ""
echo "--- Stage 3: mImgtbl (projected) ---"
T3_START=\$(date +%s)
mImgtbl "\${PROJ_DIR}" "\${WORK_DIR}/proj_images.tbl"
T3_END=\$(date +%s)
T3=\$((T3_END - T3_START))
echo "mImgtbl(proj) time: \${T3}s"

# ── Stage 4: mOverlaps (identify pairs) ───────────────────────────────────
echo ""
echo "--- Stage 4: mOverlaps ---"
T4_START=\$(date +%s)
mOverlaps "\${WORK_DIR}/proj_images.tbl" "\${WORK_DIR}/diffs.tbl"
T4_END=\$(date +%s)
T4=\$((T4_END - T4_START))
N_PAIRS=\$(wc -l < "\${WORK_DIR}/diffs.tbl" || echo "0")
echo "mOverlaps time: \${T4}s (\${N_PAIRS} pairs)"

# ── Stage 5: mDiffExec (differencing — parallel per pair) ─────────────────
echo ""
echo "--- Stage 5: mDiffExec ---"
T5_START=\$(date +%s)
mDiffExec -p "\${PROJ_DIR}" "\${WORK_DIR}/diffs.tbl" "${HDR_FILE}" "\${DIFF_DIR}"
T5_END=\$(date +%s)
T5=\$((T5_END - T5_START))
echo "mDiffExec time: \${T5}s"

# ── Stage 6: mFitExec (plane fitting — parallel per pair) ─────────────────
echo ""
echo "--- Stage 6: mFitExec ---"
T6_START=\$(date +%s)
mFitExec "\${WORK_DIR}/diffs.tbl" "\${WORK_DIR}/fits.tbl" "\${DIFF_DIR}"
T6_END=\$(date +%s)
T6=\$((T6_END - T6_START))
echo "mFitExec time: \${T6}s"

# ── Stage 7: mBgModel (background modeling — serial) ──────────────────────
echo ""
echo "--- Stage 7: mBgModel ---"
T7_START=\$(date +%s)
mBgModel "\${WORK_DIR}/proj_images.tbl" "\${WORK_DIR}/fits.tbl" "\${WORK_DIR}/corrections.tbl"
T7_END=\$(date +%s)
T7=\$((T7_END - T7_START))
echo "mBgModel time: \${T7}s"

# ── Stage 8: mBgExec (background correction — parallel per image) ─────────
echo ""
echo "--- Stage 8: mBgExec ---"
T8_START=\$(date +%s)
mBgExec -p "\${PROJ_DIR}" "\${WORK_DIR}/proj_images.tbl" "\${WORK_DIR}/corrections.tbl" "\${CORR_DIR}"
T8_END=\$(date +%s)
T8=\$((T8_END - T8_START))
echo "mBgExec time: \${T8}s"

# ── Stage 9: mImgtbl (corrected catalog) ──────────────────────────────────
echo ""
echo "--- Stage 9: mImgtbl (corrected) ---"
T9_START=\$(date +%s)
mImgtbl "\${CORR_DIR}" "\${WORK_DIR}/corr_images.tbl"
T9_END=\$(date +%s)
T9=\$((T9_END - T9_START))
echo "mImgtbl(corr) time: \${T9}s"

# ── Stage 10: mAdd (coaddition — serial) ──────────────────────────────────
echo ""
echo "--- Stage 10: mAdd ---"
T10_START=\$(date +%s)
mAdd -p "\${CORR_DIR}" "\${WORK_DIR}/corr_images.tbl" "${HDR_FILE}" "\${WORK_DIR}/mosaic.fits"
T10_END=\$(date +%s)
T10=\$((T10_END - T10_START))
echo "mAdd time: \${T10}s"

# ── Collect results ───────────────────────────────────────────────────────
T_TOTAL=\$((T10_END - T1_START))

# Measure intermediate data sizes
PROJ_SIZE=\$(du -sb "\${PROJ_DIR}" | cut -f1)
DIFF_SIZE=\$(du -sb "\${DIFF_DIR}" | cut -f1)
CORR_SIZE=\$(du -sb "\${CORR_DIR}" | cut -f1)
MOSAIC_SIZE=\$(stat --printf="%s" "\${WORK_DIR}/mosaic.fits" 2>/dev/null || echo "0")
TOTAL_INTERMEDIATE=\$((PROJ_SIZE + DIFF_SIZE + CORR_SIZE + MOSAIC_SIZE))

STATUS="SUCCESS"
if [[ ! -f "\${WORK_DIR}/mosaic.fits" ]]; then
    STATUS="FAILED"
fi

{
echo "RESULT: size=${SIZE}, backend=${STORAGE}, nodes=${NODES}"
echo "mImgtbl_time_s=\${T1}"
echo "mProjExec_time_s=\${T2}"
echo "mImgtbl_proj_time_s=\${T3}"
echo "mOverlaps_time_s=\${T4}"
echo "mDiffExec_time_s=\${T5}"
echo "mFitExec_time_s=\${T6}"
echo "mBgModel_time_s=\${T7}"
echo "mBgExec_time_s=\${T8}"
echo "mImgtbl_corr_time_s=\${T9}"
echo "mAdd_time_s=\${T10}"
echo "total_time_s=\${T_TOTAL}"
echo "n_images=${FITS_COUNT}"
echo "n_pairs=\${N_PAIRS}"
echo "proj_bytes=\${PROJ_SIZE}"
echo "diff_bytes=\${DIFF_SIZE}"
echo "corr_bytes=\${CORR_SIZE}"
echo "mosaic_bytes=\${MOSAIC_SIZE}"
echo "total_intermediate_bytes=\${TOTAL_INTERMEDIATE}"
echo "status=\${STATUS}"
} > "${RESULTS_DIR}/result.txt"

echo ""
echo "=== Results ==="
cat "${RESULTS_DIR}/result.txt"
echo ""
echo "End: \$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Cleanup handled by trap
SLURM_BODY

echo "Submitting: sbatch ${JOB_SCRIPT}"
sbatch "${JOB_SCRIPT}"
echo "Monitor: tail -f ${RESULTS_DIR}/slurm_*.out"
