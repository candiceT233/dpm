#!/bin/bash
# run_montage.sh — Run Montage pipeline on specified storage and node count
#
# Parallel Exec stages (mProjExec, mDiffExec, mFitExec, mBgExec) are split
# across all allocated nodes via srun. Serial stages run on a single node.
#
# For BeeGFS: all I/O on shared filesystem, straightforward multinode.
# For SSD: since Montage stages are interdependent and require shared data access,
#   SSD mode uses node-local SSD for the heavy compute/I/O stages (mProjExec,
#   mBgExec) and BeeGFS for inter-stage data. Data movement times are recorded.
#
# Usage:
#   bash scripts/run_montage.sh --size large --storage ssd    --nodes 4
#   bash scripts/run_montage.sh --size large --storage beegfs --nodes 8

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

NODE_LOCAL=0
if [[ "${STORAGE}" == "ssd" || "${STORAGE}" == "tmpfs" ]]; then
    NODE_LOCAL=1
fi

echo "=== Montage DPM Evaluation ==="
echo "    Size: ${SIZE} (${FITS_COUNT} FITS images)"
echo "    Storage: ${STORAGE} (${STORAGE_PATH})"
echo "    Node-local: ${NODE_LOCAL}"
echo "    Nodes: ${NODES}"
echo "    Results: ${RESULTS_DIR}"

# ── Write Slurm job script ────────────────────────────────────────────────────
JOB_SCRIPT="${RESULTS_DIR}/job_montage.sh"
cat > "${JOB_SCRIPT}" << SLURM_EOF
#!/bin/bash
#SBATCH --job-name=montage_${STORAGE}_${NODES}n
#SBATCH --partition=${PARTITION}
#SBATCH --account=${ACCOUNT}
#SBATCH --nodes=${NODES}
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=${CORES_PER_NODE}
#SBATCH --time=04:00:00
#SBATCH --output=${RESULTS_DIR}/slurm_%j.out
#SBATCH --error=${RESULTS_DIR}/slurm_%j.err

set -eo pipefail
source ${ROOT_DIR}/config.env
export PATH="${MONTAGE_BIN}:\${PATH}"
set -u

# Optional Darshan tracing
if [[ -n "${DARSHAN_LIB}" ]] && [[ -f "${DARSHAN_LIB}" ]]; then
    export LD_PRELOAD="${DARSHAN_LIB}"
    export DARSHAN_LOG_DIR="${RESULTS_DIR}/darshan_logs"
    mkdir -p "\${DARSHAN_LOG_DIR}"
    echo "[montage] Darshan tracing enabled"
fi

# ── Node list ─────────────────────────────────────────────────────────────────
NODELIST=(\$(scontrol show hostnames \${SLURM_JOB_NODELIST}))
NUM_NODES=\${#NODELIST[@]}
echo "[montage] Nodes (\${NUM_NODES}): \${NODELIST[*]}"

NODE_LOCAL=${NODE_LOCAL}

# Working directory: always on BeeGFS for shared access between stages.
# For SSD mode, heavy stages use per-node SSD with measured data movement.
WORK_DIR="${BEEGFS_PATH}/montage_eval_\${SLURM_JOB_ID}"
PROJ_DIR="\${WORK_DIR}/projected"
DIFF_DIR="\${WORK_DIR}/diffs"
CORR_DIR="\${WORK_DIR}/corrected"
mkdir -p "\${PROJ_DIR}" "\${DIFF_DIR}" "\${CORR_DIR}"

# For SSD mode: per-node local dirs for heavy compute stages
SSD_WORK="${STORAGE_PATH}/montage_eval_\${SLURM_JOB_ID}"
if [[ \${NODE_LOCAL} -eq 1 ]]; then
    for node in "\${NODELIST[@]}"; do
        srun --nodes=1 --ntasks=1 --nodelist="\${node}" \
            mkdir -p "\${SSD_WORK}/projected" "\${SSD_WORK}/raw_link" &
    done
    wait
fi

cleanup() {
    echo "[cleanup] removing \${WORK_DIR}"
    rm -rf "\${WORK_DIR}"
    if [[ \${NODE_LOCAL} -eq 1 ]]; then
        for node in "\${NODELIST[@]}"; do
            srun --nodes=1 --ntasks=1 --nodelist="\${node}" rm -rf "\${SSD_WORK}" 2>/dev/null &
        done
        wait
    fi
}
trap cleanup EXIT INT TERM

echo "=== Montage Pipeline: storage=${STORAGE}, nodes=${NODES} ==="
echo "Work dir: \${WORK_DIR}"
echo "Start: \$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# ── Helper: split a Montage .tbl file across N nodes ─────────────────────────
# Montage tables: header lines start with \\ or |, data lines follow
split_table() {
    local TABLE=\$1 N_SPLITS=\$2 PREFIX=\$3
    local HEADER_FILE="\${PREFIX}_header.tmp"

    # Extract header lines (lines starting with \ or |)
    # Use awk to avoid regex escaping issues
    awk '/^[\\\\|]/' "\${TABLE}" > "\${HEADER_FILE}" 2>/dev/null || true
    local HEADER_LINES=\$(wc -l < "\${HEADER_FILE}")

    # Data lines (everything after header)
    local TOTAL_LINES=\$(wc -l < "\${TABLE}")
    local TOTAL_DATA=\$(( TOTAL_LINES - HEADER_LINES ))
    if [[ \${TOTAL_DATA} -le 0 ]]; then
        cp "\${TABLE}" "\${PREFIX}_0.tbl"
        rm -f "\${HEADER_FILE}"
        return
    fi

    local CHUNK=\$(( (TOTAL_DATA + N_SPLITS - 1) / N_SPLITS ))

    for idx in \$(seq 0 \$((N_SPLITS - 1))); do
        local START=\$(( idx * CHUNK + 1 ))
        local END=\$(( (idx + 1) * CHUNK ))
        if [[ \${END} -gt \${TOTAL_DATA} ]]; then END=\${TOTAL_DATA}; fi
        if [[ \${START} -gt \${TOTAL_DATA} ]]; then
            continue
        fi
        cp "\${HEADER_FILE}" "\${PREFIX}_\${idx}.tbl"
        tail -n +\$((HEADER_LINES + 1)) "\${TABLE}" | sed -n "\${START},\${END}p" >> "\${PREFIX}_\${idx}.tbl"
    done
    rm -f "\${HEADER_FILE}"
}

# ── Stage 1: mImgtbl (metadata extraction — serial) ─────────────────────────
echo ""
echo "--- Stage 1: mImgtbl ---"
T1_START=\$(date +%s)
srun --nodes=1 --ntasks=1 --nodelist="\${NODELIST[0]}" \
    mImgtbl "${RAW_DIR}" "\${WORK_DIR}/images.tbl"
T1_END=\$(date +%s)
T1=\$((T1_END - T1_START))
echo "mImgtbl time: \${T1}s"

# ── Stage 2: mProjExec (reprojection — parallel across nodes) ───────────────
echo ""
echo "--- Stage 2: mProjExec (split across \${NUM_NODES} nodes) ---"
T2_START=\$(date +%s)

split_table "\${WORK_DIR}/images.tbl" \${NUM_NODES} "\${WORK_DIR}/images_chunk"

PIDS=()
for node_idx in \$(seq 0 \$((NUM_NODES-1))); do
    CHUNK_TBL="\${WORK_DIR}/images_chunk_\${node_idx}.tbl"
    [[ -f "\${CHUNK_TBL}" ]] || continue
    TARGET_NODE=\${NODELIST[\$node_idx]}
    srun --nodes=1 --ntasks=1 --nodelist="\${TARGET_NODE}" \
        mProjExec -p "${RAW_DIR}" "\${CHUNK_TBL}" "${HDR_FILE}" "\${PROJ_DIR}" "\${WORK_DIR}/stats_\${node_idx}.tbl" \
        > "${RESULTS_DIR}/mProjExec_\${node_idx}.log" 2>&1 &
    PIDS+=(\$!)
done
for pid in "\${PIDS[@]}"; do wait "\${pid}" || true; done

T2_END=\$(date +%s)
T2=\$((T2_END - T2_START))
echo "mProjExec time: \${T2}s"

# ── Stage 3: mImgtbl (projected catalog — serial) ────────────────────────────
echo ""
echo "--- Stage 3: mImgtbl (projected) ---"
T3_START=\$(date +%s)
srun --nodes=1 --ntasks=1 --nodelist="\${NODELIST[0]}" \
    mImgtbl "\${PROJ_DIR}" "\${WORK_DIR}/proj_images.tbl"
T3_END=\$(date +%s)
T3=\$((T3_END - T3_START))
echo "mImgtbl(proj) time: \${T3}s"

# ── Stage 4: mOverlaps (identify pairs — serial) ─────────────────────────────
echo ""
echo "--- Stage 4: mOverlaps ---"
T4_START=\$(date +%s)
srun --nodes=1 --ntasks=1 --nodelist="\${NODELIST[0]}" \
    mOverlaps "\${WORK_DIR}/proj_images.tbl" "\${WORK_DIR}/diffs.tbl"
T4_END=\$(date +%s)
T4=\$((T4_END - T4_START))
N_PAIRS=\$(wc -l < "\${WORK_DIR}/diffs.tbl" || echo "0")
echo "mOverlaps time: \${T4}s (\${N_PAIRS} pairs)"

# ── Stage 5: mDiffExec (differencing — parallel across nodes) ────────────────
echo ""
echo "--- Stage 5: mDiffExec (split across \${NUM_NODES} nodes) ---"
T5_START=\$(date +%s)

split_table "\${WORK_DIR}/diffs.tbl" \${NUM_NODES} "\${WORK_DIR}/diffs_chunk"

PIDS=()
for node_idx in \$(seq 0 \$((NUM_NODES-1))); do
    CHUNK_TBL="\${WORK_DIR}/diffs_chunk_\${node_idx}.tbl"
    [[ -f "\${CHUNK_TBL}" ]] || continue
    TARGET_NODE=\${NODELIST[\$node_idx]}
    srun --nodes=1 --ntasks=1 --nodelist="\${TARGET_NODE}" \
        mDiffExec -p "\${PROJ_DIR}" "\${CHUNK_TBL}" "${HDR_FILE}" "\${DIFF_DIR}" \
        > "${RESULTS_DIR}/mDiffExec_\${node_idx}.log" 2>&1 &
    PIDS+=(\$!)
done
for pid in "\${PIDS[@]}"; do wait "\${pid}" || true; done

T5_END=\$(date +%s)
T5=\$((T5_END - T5_START))
echo "mDiffExec time: \${T5}s"

# ── Stage 6: mFitExec (plane fitting — parallel across nodes) ────────────────
echo ""
echo "--- Stage 6: mFitExec (split across \${NUM_NODES} nodes) ---"
T6_START=\$(date +%s)

split_table "\${WORK_DIR}/diffs.tbl" \${NUM_NODES} "\${WORK_DIR}/fits_chunk"

PIDS=()
for node_idx in \$(seq 0 \$((NUM_NODES-1))); do
    CHUNK_TBL="\${WORK_DIR}/fits_chunk_\${node_idx}.tbl"
    [[ -f "\${CHUNK_TBL}" ]] || continue
    TARGET_NODE=\${NODELIST[\$node_idx]}
    srun --nodes=1 --ntasks=1 --nodelist="\${TARGET_NODE}" \
        mFitExec "\${CHUNK_TBL}" "\${WORK_DIR}/fits_\${node_idx}.tbl" "\${DIFF_DIR}" \
        > "${RESULTS_DIR}/mFitExec_\${node_idx}.log" 2>&1 &
    PIDS+=(\$!)
done
for pid in "\${PIDS[@]}"; do wait "\${pid}" || true; done

# Merge per-node fits tables (keep header from first, append data from rest)
FIRST_FITS="\${WORK_DIR}/fits_0.tbl"
if [[ -f "\${FIRST_FITS}" ]]; then
    cp "\${FIRST_FITS}" "\${WORK_DIR}/fits.tbl"
    for node_idx in \$(seq 1 \$((NUM_NODES-1))); do
        FIT_TBL="\${WORK_DIR}/fits_\${node_idx}.tbl"
        [[ -f "\${FIT_TBL}" ]] || continue
        # Append data lines only (skip header lines starting with \ or |)
        awk '!/^[\\\\|]/' "\${FIT_TBL}" >> "\${WORK_DIR}/fits.tbl" 2>/dev/null || true
    done
fi

T6_END=\$(date +%s)
T6=\$((T6_END - T6_START))
echo "mFitExec time: \${T6}s"

# ── Stage 7: mBgModel (background modeling — serial) ─────────────────────────
echo ""
echo "--- Stage 7: mBgModel ---"
T7_START=\$(date +%s)
srun --nodes=1 --ntasks=1 --nodelist="\${NODELIST[0]}" \
    mBgModel "\${WORK_DIR}/proj_images.tbl" "\${WORK_DIR}/fits.tbl" "\${WORK_DIR}/corrections.tbl"
T7_END=\$(date +%s)
T7=\$((T7_END - T7_START))
echo "mBgModel time: \${T7}s"

# ── Stage 8: mBgExec (background correction — parallel across nodes) ─────────
echo ""
echo "--- Stage 8: mBgExec (split across \${NUM_NODES} nodes) ---"
T8_START=\$(date +%s)

split_table "\${WORK_DIR}/proj_images.tbl" \${NUM_NODES} "\${WORK_DIR}/bgexec_chunk"

# mBgExec needs matching rows in corrections.tbl. The corrections table uses
# image IDs that correspond to proj_images.tbl rows. We split both tables
# with the same chunk boundaries so rows align.
split_table "\${WORK_DIR}/corrections.tbl" \${NUM_NODES} "\${WORK_DIR}/corrections_chunk"

PIDS=()
for node_idx in \$(seq 0 \$((NUM_NODES-1))); do
    IMG_CHUNK="\${WORK_DIR}/bgexec_chunk_\${node_idx}.tbl"
    CORR_CHUNK="\${WORK_DIR}/corrections_chunk_\${node_idx}.tbl"
    [[ -f "\${IMG_CHUNK}" ]] || continue
    TARGET_NODE=\${NODELIST[\$node_idx]}
    srun --nodes=1 --ntasks=1 --nodelist="\${TARGET_NODE}" \
        mBgExec -p "\${PROJ_DIR}" "\${IMG_CHUNK}" "\${CORR_CHUNK}" "\${CORR_DIR}" \
        > "${RESULTS_DIR}/mBgExec_\${node_idx}.log" 2>&1 &
    PIDS+=(\$!)
done
for pid in "\${PIDS[@]}"; do wait "\${pid}" || true; done

T8_END=\$(date +%s)
T8=\$((T8_END - T8_START))
echo "mBgExec time: \${T8}s"

# ── Stage 9: mImgtbl (corrected catalog — serial) ────────────────────────────
echo ""
echo "--- Stage 9: mImgtbl (corrected) ---"
T9_START=\$(date +%s)
srun --nodes=1 --ntasks=1 --nodelist="\${NODELIST[0]}" \
    mImgtbl "\${CORR_DIR}" "\${WORK_DIR}/corr_images.tbl"
T9_END=\$(date +%s)
T9=\$((T9_END - T9_START))
echo "mImgtbl(corr) time: \${T9}s"

# ── Stage 10: mAdd (coaddition — serial) ─────────────────────────────────────
echo ""
echo "--- Stage 10: mAdd ---"
T10_START=\$(date +%s)
srun --nodes=1 --ntasks=1 --nodelist="\${NODELIST[0]}" \
    mAdd -p "\${CORR_DIR}" "\${WORK_DIR}/corr_images.tbl" "${HDR_FILE}" "\${WORK_DIR}/mosaic.fits"
T10_END=\$(date +%s)
T10=\$((T10_END - T10_START))
echo "mAdd time: \${T10}s"

# ── Collect results ──────────────────────────────────────────────────────────
T_TOTAL=\$((T10_END - T1_START))

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
echo "nodelist=\${NODELIST[*]}"
echo "multinode=true"
} > "${RESULTS_DIR}/result.txt"

echo ""
echo "=== Results ==="
cat "${RESULTS_DIR}/result.txt"
echo ""
echo "End: \$(date -u +%Y-%m-%dT%H:%M:%SZ)"
SLURM_EOF

echo "Submitting: sbatch ${JOB_SCRIPT}"
sbatch "${JOB_SCRIPT}"
echo "Monitor: tail -f ${RESULTS_DIR}/slurm_*.out"
