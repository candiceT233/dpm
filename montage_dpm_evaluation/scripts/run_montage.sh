#!/bin/bash
# run_montage.sh — Run Montage pipeline on specified storage and node count
#
# Parallel stages use individual Montage commands (mProject, mDiff, mFitplane,
# mBackground) distributed across all nodes via srun --ntasks=1. This gives
# Slurm-visible task distribution instead of relying on internal fork parallelism.
#
# For BeeGFS: all I/O on shared filesystem.
# For SSD/tmpfs: heavy stages on per-node local storage with measured staging.
#
# Usage:
#   bash scripts/run_montage.sh --size small --storage beegfs --nodes 4
#   bash scripts/run_montage.sh --size large --storage ssd    --nodes 8

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

case "${STORAGE}" in
    ssd)    STORAGE_PATH="${LOCAL_SSD_PATH}" ;;
    beegfs) STORAGE_PATH="${BEEGFS_PATH}"    ;;
    tmpfs)  STORAGE_PATH="${TMPFS_PATH}"     ;;
    *)      echo "Unknown storage: ${STORAGE}"; exit 1 ;;
esac

NODE_LOCAL=0
if [[ "${STORAGE}" == "ssd" || "${STORAGE}" == "tmpfs" ]]; then
    NODE_LOCAL=1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUN_ID="${STORAGE}_${SIZE}_${NODES}n_${TIMESTAMP}"
RESULTS_DIR="${ROOT_DIR}/results/${RUN_ID}"
mkdir -p "${RESULTS_DIR}"

DATA_DIR="${ROOT_DIR}/data/${SIZE}"
RAW_DIR="${DATA_DIR}/raw_images"
HDR_FILE="${DATA_DIR}/region.hdr"

if [[ ! -f "${HDR_FILE}" ]]; then
    echo "ERROR: region.hdr not found at ${HDR_FILE}"; exit 1
fi

FITS_COUNT=$(ls "${RAW_DIR}"/*.fits 2>/dev/null | wc -l)
if [[ "${FITS_COUNT}" -eq 0 ]]; then
    echo "ERROR: No FITS files in ${RAW_DIR}"; exit 1
fi

TASKS_PER_NODE=${CORES_PER_NODE}

echo "=== Montage DPM Evaluation ==="
echo "    Size: ${SIZE} (${FITS_COUNT} FITS images)"
echo "    Storage: ${STORAGE} (${STORAGE_PATH})"
echo "    Nodes: ${NODES}, Tasks/node: ${TASKS_PER_NODE}"
echo "    Results: ${RESULTS_DIR}"

# ── Write Slurm job script ────────────────────────────────────────────────────
JOB_SCRIPT="${RESULTS_DIR}/job_montage.sh"
cat > "${JOB_SCRIPT}" << SLURM_EOF
#!/bin/bash
#SBATCH --job-name=montage_${STORAGE}_${NODES}n
#SBATCH --partition=${PARTITION}
#SBATCH --account=${ACCOUNT}
#SBATCH --nodes=${NODES}
#SBATCH --ntasks-per-node=${TASKS_PER_NODE}
#SBATCH --time=04:00:00
#SBATCH --output=${RESULTS_DIR}/slurm_%j.out
#SBATCH --error=${RESULTS_DIR}/slurm_%j.err

set -eo pipefail
source ${ROOT_DIR}/config.env
export PATH="${MONTAGE_BIN}:\${PATH}"
set -u

# ── Darshan I/O tracing (optional) ────────────────────────────────────────────
if [[ -n "${DARSHAN_LIB}" ]] && [[ -f "${DARSHAN_LIB}" ]]; then
    export LD_PRELOAD="${DARSHAN_LIB}"
    export DARSHAN_ENABLE_NONMPI=1
    # Darshan uses compiled-in default log path: /qfs/people/tang584/experiments/darshan-logs/YYYY/MM/DD/
    DARSHAN_DEFAULT_LOG="/qfs/people/tang584/experiments/darshan-logs/\$(date +%Y)/\$(date +%-m)/\$(date +%-d)"
    mkdir -p "\${DARSHAN_DEFAULT_LOG}"
    echo "[montage] Darshan tracing enabled → \${DARSHAN_DEFAULT_LOG}"
fi

# ── Node list ─────────────────────────────────────────────────────────────────
NODELIST=(\$(scontrol show hostnames \${SLURM_JOB_NODELIST}))
NUM_NODES=\${#NODELIST[@]}
TOTAL_SLOTS=\$((NUM_NODES * ${TASKS_PER_NODE}))
echo "[montage] Nodes (\${NUM_NODES}): \${NODELIST[*]}"
echo "[montage] Tasks/node: ${TASKS_PER_NODE}, total slots: \${TOTAL_SLOTS}"

NODE_LOCAL=${NODE_LOCAL}
WORK_DIR="${BEEGFS_PATH}/montage_eval_\${SLURM_JOB_ID}"
PROJ_DIR="\${WORK_DIR}/projected"
DIFF_DIR="\${WORK_DIR}/diffs"
CORR_DIR="\${WORK_DIR}/corrected"
mkdir -p "\${PROJ_DIR}" "\${DIFF_DIR}" "\${CORR_DIR}"

SSD_WORK="${STORAGE_PATH}/montage_eval_\${SLURM_JOB_ID}"
if [[ \${NODE_LOCAL} -eq 1 ]]; then
    for node in "\${NODELIST[@]}"; do
        srun --nodes=1 --ntasks=1 --nodelist="\${node}" \
            mkdir -p "\${SSD_WORK}/projected" "\${SSD_WORK}/raw_link" "\${SSD_WORK}/corrected" &
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

# Helper: round-robin node assignment
node_for_idx() { echo "\${NODELIST[\$(( \$1 % NUM_NODES ))]}"; }

echo "=== Montage Pipeline: storage=${STORAGE}, nodes=${NODES} ==="
echo "Start: \$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# ── Stage 1: mImgtbl (serial) ────────────────────────────────────────────────
echo ""; echo "--- Stage 1: mImgtbl ---"
T1_START=\$(date +%s)
srun --nodes=1 --ntasks=1 --nodelist="\${NODELIST[0]}" \
    mImgtbl "${RAW_DIR}" "\${WORK_DIR}/images.tbl"
T1_END=\$(date +%s); T1=\$((T1_END - T1_START))
echo "mImgtbl time: \${T1}s"

# Build file list from images.tbl (data lines, last column = full path)
mapfile -t IMG_FILES < <(awk '!/^[\\\\|]/' "\${WORK_DIR}/images.tbl" | awk '{print \$NF}')
N_IMAGES=\${#IMG_FILES[@]}
echo "Images to project: \${N_IMAGES}"

# ── SSD stage-in 1: copy raw FITS to per-node SSD ────────────────────────────
STAGEIN1_TIME=0
if [[ \${NODE_LOCAL} -eq 1 ]]; then
    echo ""; echo "--- Stage-in 1: raw FITS → per-node SSD ---"
    T_SI1_START=\$(date +%s)
    # Generate per-node copy scripts
    for node_idx in \$(seq 0 \$((NUM_NODES-1))); do
        echo "#!/bin/bash" > "\${WORK_DIR}/stagein1_node\${node_idx}.sh"
    done
    for i in \$(seq 0 \$((N_IMAGES-1))); do
        node_idx=\$((i % NUM_NODES))
        echo "cp \${IMG_FILES[\$i]} \${SSD_WORK}/raw_link/" >> "\${WORK_DIR}/stagein1_node\${node_idx}.sh"
    done
    PIDS=()
    for node_idx in \$(seq 0 \$((NUM_NODES-1))); do
        TARGET=\${NODELIST[\$node_idx]}
        srun --nodes=1 --ntasks=1 --nodelist="\${TARGET}" \
            bash "\${WORK_DIR}/stagein1_node\${node_idx}.sh" &
        PIDS+=(\$!)
    done
    for pid in "\${PIDS[@]}"; do wait "\${pid}" || true; done
    T_SI1_END=\$(date +%s); STAGEIN1_TIME=\$((T_SI1_END - T_SI1_START))
    echo "Stage-in 1 time: \${STAGEIN1_TIME}s"
fi

# ── Stage 2: mProject (parallel, one per image) ──────────────────────────────
echo ""; echo "--- Stage 2: mProject (\${N_IMAGES} images across \${NUM_NODES} nodes) ---"
T2_START=\$(date +%s)

# Generate per-node command scripts to avoid per-task srun overhead
for node_idx in \$(seq 0 \$((NUM_NODES-1))); do
    SCRIPT="\${WORK_DIR}/mproject_node\${node_idx}.sh"
    echo "#!/bin/bash" > "\${SCRIPT}"
    chmod +x "\${SCRIPT}"
done

for i in \$(seq 0 \$((N_IMAGES-1))); do
    node_idx=\$((i % NUM_NODES))
    IN_FITS="\${IMG_FILES[\$i]}"
    BASENAME=\$(basename "\${IN_FITS}")
    OUT_FITS="hdu0_\${BASENAME}"
    if [[ \${NODE_LOCAL} -eq 1 ]]; then
        IN_PATH="\${SSD_WORK}/raw_link/\${BASENAME}"
        OUT_PATH="\${SSD_WORK}/projected/\${OUT_FITS}"
    else
        IN_PATH="\${IN_FITS}"
        OUT_PATH="\${PROJ_DIR}/\${OUT_FITS}"
    fi
    echo "mProject \${IN_PATH} \${OUT_PATH} ${HDR_FILE} > /dev/null 2>&1 &" >> "\${WORK_DIR}/mproject_node\${node_idx}.sh"
done

# Add wait at end of each script
for node_idx in \$(seq 0 \$((NUM_NODES-1))); do
    echo "wait" >> "\${WORK_DIR}/mproject_node\${node_idx}.sh"
done

# Launch one srun per node, each running its batch of mProject calls
PIDS=()
for node_idx in \$(seq 0 \$((NUM_NODES-1))); do
    TARGET=\${NODELIST[\$node_idx]}
    srun --nodes=1 --ntasks=1 --nodelist="\${TARGET}" \
        bash "\${WORK_DIR}/mproject_node\${node_idx}.sh" &
    PIDS+=(\$!)
done
PROJ_FAILED=0
for pid in "\${PIDS[@]}"; do wait "\${pid}" || PROJ_FAILED=\$((PROJ_FAILED+1)); done

T2_END=\$(date +%s); T2=\$((T2_END - T2_START))
echo "mProject time: \${T2}s (failed=\${PROJ_FAILED})"

# ── SSD stage-out 1: projected FITS → BeeGFS ─────────────────────────────────
STAGEOUT1_TIME=0
if [[ \${NODE_LOCAL} -eq 1 ]]; then
    echo "--- Stage-out 1: projected FITS per-node SSD → BeeGFS ---"
    T_SO1_START=\$(date +%s)
    PIDS=()
    for node_idx in \$(seq 0 \$((NUM_NODES-1))); do
        TARGET=\${NODELIST[\$node_idx]}
        echo "#!/bin/bash
cp \${SSD_WORK}/projected/*.fits \${PROJ_DIR}/ 2>/dev/null || true" > "\${WORK_DIR}/stageout1_node\${node_idx}.sh"
        srun --nodes=1 --ntasks=1 --nodelist="\${TARGET}" \
            bash "\${WORK_DIR}/stageout1_node\${node_idx}.sh" &
        PIDS+=(\$!)
    done
    for pid in "\${PIDS[@]}"; do wait "\${pid}" || true; done
    T_SO1_END=\$(date +%s); STAGEOUT1_TIME=\$((T_SO1_END - T_SO1_START))
    echo "Stage-out 1 time: \${STAGEOUT1_TIME}s"
fi

# ── Stage 3: mImgtbl projected (serial) ──────────────────────────────────────
echo ""; echo "--- Stage 3: mImgtbl (projected) ---"
T3_START=\$(date +%s)
srun --nodes=1 --ntasks=1 --nodelist="\${NODELIST[0]}" \
    mImgtbl "\${PROJ_DIR}" "\${WORK_DIR}/proj_images.tbl"
T3_END=\$(date +%s); T3=\$((T3_END - T3_START))
echo "mImgtbl(proj) time: \${T3}s"

# ── Stage 4: mOverlaps (serial) ──────────────────────────────────────────────
echo ""; echo "--- Stage 4: mOverlaps ---"
T4_START=\$(date +%s)
srun --nodes=1 --ntasks=1 --nodelist="\${NODELIST[0]}" \
    mOverlaps "\${WORK_DIR}/proj_images.tbl" "\${WORK_DIR}/diffs.tbl"
T4_END=\$(date +%s); T4=\$((T4_END - T4_START))
N_PAIRS=\$(awk '!/^[\\\\|]/' "\${WORK_DIR}/diffs.tbl" | wc -l)
echo "mOverlaps time: \${T4}s (\${N_PAIRS} pairs)"

# ── Stage 5: mDiff (parallel, one per pair, batched per node) ─────────────────
echo ""; echo "--- Stage 5: mDiff (\${N_PAIRS} pairs across \${NUM_NODES} nodes) ---"
T5_START=\$(date +%s)

# Generate per-node mDiff scripts
for node_idx in \$(seq 0 \$((NUM_NODES-1))); do
    echo "#!/bin/bash" > "\${WORK_DIR}/mdiff_node\${node_idx}.sh"
done

IDX=0
while IFS= read -r line; do
    PLUS=\$(echo "\${line}" | awk '{print \$3}')
    MINUS=\$(echo "\${line}" | awk '{print \$4}')
    DIFF_NAME=\$(echo "\${line}" | awk '{print \$5}')
    node_idx=\$((IDX % NUM_NODES))
    echo "mDiff \${PLUS} \${MINUS} \${DIFF_DIR}/\${DIFF_NAME} ${HDR_FILE} > /dev/null 2>&1 &" >> "\${WORK_DIR}/mdiff_node\${node_idx}.sh"
    IDX=\$((IDX+1))
done < <(awk '!/^[\\\\|]/' "\${WORK_DIR}/diffs.tbl")

for node_idx in \$(seq 0 \$((NUM_NODES-1))); do
    echo "wait" >> "\${WORK_DIR}/mdiff_node\${node_idx}.sh"
done

PIDS=()
for node_idx in \$(seq 0 \$((NUM_NODES-1))); do
    TARGET=\${NODELIST[\$node_idx]}
    srun --nodes=1 --ntasks=1 --nodelist="\${TARGET}" \
        bash "\${WORK_DIR}/mdiff_node\${node_idx}.sh" &
    PIDS+=(\$!)
done
for pid in "\${PIDS[@]}"; do wait "\${pid}" || true; done

T5_END=\$(date +%s); T5=\$((T5_END - T5_START))
echo "mDiff time: \${T5}s"

# ── Stage 6: mFitExec (serial, fast — mFitplane output is hard to reassemble) ─
echo ""; echo "--- Stage 6: mFitExec ---"
T6_START=\$(date +%s)
srun --nodes=1 --ntasks=1 --nodelist="\${NODELIST[0]}" \
    mFitExec "\${WORK_DIR}/diffs.tbl" "\${WORK_DIR}/fits.tbl" "\${DIFF_DIR}"
T6_END=\$(date +%s); T6=\$((T6_END - T6_START))
echo "mFitExec time: \${T6}s"

# ── Stage 7: mBgModel (serial) ───────────────────────────────────────────────
echo ""; echo "--- Stage 7: mBgModel ---"
T7_START=\$(date +%s)
srun --nodes=1 --ntasks=1 --nodelist="\${NODELIST[0]}" \
    mBgModel "\${WORK_DIR}/proj_images.tbl" "\${WORK_DIR}/fits.tbl" "\${WORK_DIR}/corrections.tbl"
T7_END=\$(date +%s); T7=\$((T7_END - T7_START))
echo "mBgModel time: \${T7}s"

# ── SSD stage-in 2: projected FITS → per-node SSD for mBackground ────────────
STAGEIN2_TIME=0
if [[ \${NODE_LOCAL} -eq 1 ]]; then
    echo ""; echo "--- Stage-in 2: projected FITS → per-node SSD ---"
    T_SI2_START=\$(date +%s)
    PIDS=()
    for node_idx in \$(seq 0 \$((NUM_NODES-1))); do
        TARGET=\${NODELIST[\$node_idx]}
        echo "#!/bin/bash
mkdir -p \${SSD_WORK}/corrected
cp \${PROJ_DIR}/*.fits \${SSD_WORK}/projected/" > "\${WORK_DIR}/stagein2_node\${node_idx}.sh"
        srun --nodes=1 --ntasks=1 --nodelist="\${TARGET}" \
            bash "\${WORK_DIR}/stagein2_node\${node_idx}.sh" &
        PIDS+=(\$!)
    done
    for pid in "\${PIDS[@]}"; do wait "\${pid}" || true; done
    T_SI2_END=\$(date +%s); STAGEIN2_TIME=\$((T_SI2_END - T_SI2_START))
    echo "Stage-in 2 time: \${STAGEIN2_TIME}s"
fi

# ── Stage 8: mBackground (parallel, one per image, batched per node) ──────────
echo ""; echo "--- Stage 8: mBackground across \${NUM_NODES} nodes ---"
T8_START=\$(date +%s)

mapfile -t PROJ_FILES < <(awk '!/^[\\\\|]/' "\${WORK_DIR}/proj_images.tbl" | awk '{print \$NF}')
N_PROJ=\${#PROJ_FILES[@]}
echo "  Images to correct: \${N_PROJ}"

# Parse correction coefficients (id, a, b, c) into arrays
mapfile -t CORR_LINES < <(awk '!/^[\\\\|]/' "\${WORK_DIR}/corrections.tbl")

# Generate per-node mBackground scripts using explicit A B C coefficients
for node_idx in \$(seq 0 \$((NUM_NODES-1))); do
    echo "#!/bin/bash" > "\${WORK_DIR}/mbg_node\${node_idx}.sh"
done

for i in \$(seq 0 \$((N_PROJ-1))); do
    node_idx=\$((i % NUM_NODES))
    BASENAME=\$(basename "\${PROJ_FILES[\$i]}")
    # Extract A B C from corrections.tbl (columns: id, a, b, c)
    CORR_A=\$(echo "\${CORR_LINES[\$i]}" | awk '{print \$2}')
    CORR_B=\$(echo "\${CORR_LINES[\$i]}" | awk '{print \$3}')
    CORR_C=\$(echo "\${CORR_LINES[\$i]}" | awk '{print \$4}')
    if [[ \${NODE_LOCAL} -eq 1 ]]; then
        IN_PATH="\${SSD_WORK}/projected/\${BASENAME}"
        OUT_PATH="\${SSD_WORK}/corrected/\${BASENAME}"
    else
        IN_PATH="\${PROJ_DIR}/\${BASENAME}"
        OUT_PATH="\${CORR_DIR}/\${BASENAME}"
    fi
    echo "mBackground \${IN_PATH} \${OUT_PATH} \${CORR_A} \${CORR_B} \${CORR_C} > /dev/null 2>&1 &" >> "\${WORK_DIR}/mbg_node\${node_idx}.sh"
done

for node_idx in \$(seq 0 \$((NUM_NODES-1))); do
    echo "wait" >> "\${WORK_DIR}/mbg_node\${node_idx}.sh"
done

PIDS=()
for node_idx in \$(seq 0 \$((NUM_NODES-1))); do
    TARGET=\${NODELIST[\$node_idx]}
    srun --nodes=1 --ntasks=1 --nodelist="\${TARGET}" \
        bash "\${WORK_DIR}/mbg_node\${node_idx}.sh" &
    PIDS+=(\$!)
done
BG_FAILED=0
for pid in "\${PIDS[@]}"; do wait "\${pid}" || BG_FAILED=\$((BG_FAILED+1)); done

T8_END=\$(date +%s); T8=\$((T8_END - T8_START))
echo "mBackground time: \${T8}s (failed=\${BG_FAILED})"

# ── SSD stage-out 2: corrected FITS → BeeGFS ─────────────────────────────────
STAGEOUT2_TIME=0
if [[ \${NODE_LOCAL} -eq 1 ]]; then
    echo "--- Stage-out 2: corrected FITS per-node SSD → BeeGFS ---"
    T_SO2_START=\$(date +%s)
    PIDS=()
    for node_idx in \$(seq 0 \$((NUM_NODES-1))); do
        TARGET=\${NODELIST[\$node_idx]}
        echo "#!/bin/bash
cp \${SSD_WORK}/corrected/*.fits \${CORR_DIR}/ 2>/dev/null || true" > "\${WORK_DIR}/stageout2_node\${node_idx}.sh"
        srun --nodes=1 --ntasks=1 --nodelist="\${TARGET}" \
            bash "\${WORK_DIR}/stageout2_node\${node_idx}.sh" &
        PIDS+=(\$!)
    done
    for pid in "\${PIDS[@]}"; do wait "\${pid}" || true; done
    T_SO2_END=\$(date +%s); STAGEOUT2_TIME=\$((T_SO2_END - T_SO2_START))
    echo "Stage-out 2 time: \${STAGEOUT2_TIME}s"
fi

# ── Stage 9: mImgtbl corrected (serial) ──────────────────────────────────────
echo ""; echo "--- Stage 9: mImgtbl (corrected) ---"
T9_START=\$(date +%s)
srun --nodes=1 --ntasks=1 --nodelist="\${NODELIST[0]}" \
    mImgtbl "\${CORR_DIR}" "\${WORK_DIR}/corr_images.tbl"
T9_END=\$(date +%s); T9=\$((T9_END - T9_START))
echo "mImgtbl(corr) time: \${T9}s"

# ── Stage 10: mAdd (serial) ──────────────────────────────────────────────────
echo ""; echo "--- Stage 10: mAdd ---"
T10_START=\$(date +%s)
srun --nodes=1 --ntasks=1 --nodelist="\${NODELIST[0]}" \
    mAdd -p "\${CORR_DIR}" "\${WORK_DIR}/corr_images.tbl" "${HDR_FILE}" "\${WORK_DIR}/mosaic.fits"
T10_END=\$(date +%s); T10=\$((T10_END - T10_START))
echo "mAdd time: \${T10}s"

# ── Collect results ──────────────────────────────────────────────────────────
T_TOTAL=\$((T10_END - T1_START))
PROJ_SIZE=\$(du -sb "\${PROJ_DIR}" | cut -f1)
DIFF_SIZE=\$(du -sb "\${DIFF_DIR}" | cut -f1)
CORR_SIZE=\$(du -sb "\${CORR_DIR}" | cut -f1)
MOSAIC_SIZE=\$(stat --printf="%s" "\${WORK_DIR}/mosaic.fits" 2>/dev/null || echo "0")
TOTAL_INTERMEDIATE=\$((PROJ_SIZE + DIFF_SIZE + CORR_SIZE + MOSAIC_SIZE))

STATUS="SUCCESS"
if [[ ! -f "\${WORK_DIR}/mosaic.fits" ]]; then STATUS="FAILED"; fi

{
echo "RESULT: size=${SIZE}, backend=${STORAGE}, nodes=${NODES}"
echo "mImgtbl_time_s=\${T1}"
echo "mProject_time_s=\${T2}"
echo "mProject_failed=\${PROJ_FAILED}"
echo "mImgtbl_proj_time_s=\${T3}"
echo "mOverlaps_time_s=\${T4}"
echo "mDiff_time_s=\${T5}"
echo "mFitExec_time_s=\${T6}"
echo "mBgModel_time_s=\${T7}"
echo "mBackground_time_s=\${T8}"
echo "mBackground_failed=\${BG_FAILED}"
echo "stagein1_time_s=\${STAGEIN1_TIME}"
echo "stageout1_time_s=\${STAGEOUT1_TIME}"
echo "stagein2_time_s=\${STAGEIN2_TIME}"
echo "stageout2_time_s=\${STAGEOUT2_TIME}"
echo "total_staging_time_s=\$((STAGEIN1_TIME + STAGEOUT1_TIME + STAGEIN2_TIME + STAGEOUT2_TIME))"
echo "mImgtbl_corr_time_s=\${T9}"
echo "mAdd_time_s=\${T10}"
echo "total_time_s=\${T_TOTAL}"
echo "n_images=${FITS_COUNT}"
echo "n_pairs=\${N_PAIRS}"
echo "tasks_per_node=${TASKS_PER_NODE}"
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
echo "End: \$(date -u +%Y-%m-%dT%H:%M:%SZ)"
SLURM_EOF

echo "Submitting: sbatch ${JOB_SCRIPT}"
sbatch "${JOB_SCRIPT}"
echo "Monitor: tail -f ${RESULTS_DIR}/slurm_*.out"
