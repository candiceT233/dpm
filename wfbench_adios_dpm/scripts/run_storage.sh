#!/bin/bash
# run_storage.sh — Run the synthetic workflow using file-based storage (DPM config)
#
# Uses IOR for I/O operations with sequential 1MB transfers for all stages,
# matching the ADIOS SST consumer's sequential read pattern for fair comparison.
# Tasks are distributed across all allocated nodes via srun.
#
# Usage:
#   bash scripts/run_storage.sh --size small  --storage tmpfs  --nodes 4
#   bash scripts/run_storage.sh --size large  --storage ssd    --nodes 4
#   bash scripts/run_storage.sh --size large  --storage beegfs --nodes 32

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"
source "${ROOT_DIR}/config.env"

# ── Parse arguments ───────────────────────────────────────────────────────────
SIZE="small"
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

# Storage is node-local (SSD/tmpfs) or shared (BeeGFS)
NODE_LOCAL=0
if [[ "${STORAGE}" == "ssd" || "${STORAGE}" == "tmpfs" ]]; then
    NODE_LOCAL=1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUN_ID="${STORAGE}_${SIZE}_${NODES}n_${TIMESTAMP}"
RESULTS_DIR="${ROOT_DIR}/results/${RUN_ID}"
mkdir -p "${RESULTS_DIR}"

echo "=== Storage run: size=${SIZE}, storage=${STORAGE}, nodes=${NODES} ==="
echo "    Storage path: ${STORAGE_PATH}"
echo "    Node-local: ${NODE_LOCAL}"
echo "    Results: ${RESULTS_DIR}"

# ── Extract metadata from workflow JSON ───────────────────────────────────────
WORKFLOW_JSON="${ROOT_DIR}/wfbench/workflow_${SIZE}_${NODES}n.json"
if [[ ! -f "${WORKFLOW_JSON}" ]]; then
    WORKFLOW_JSON="${ROOT_DIR}/wfbench/workflow_${SIZE}.json"
fi
if [[ ! -f "${WORKFLOW_JSON}" ]]; then
    echo "ERROR: ${WORKFLOW_JSON} not found."
    exit 1
fi

STAGE1_BYTES=$(python3 -c "import json; wf=json.load(open('${WORKFLOW_JSON}')); print(wf['dpmMeta']['stage1FileSizeBytes'])")
STAGE2_BYTES=$(python3 -c "import json; wf=json.load(open('${WORKFLOW_JSON}')); print(wf['dpmMeta']['stage2FileSizeBytes'])")
N_TASKS=$((NODES * TASKS_PER_NODE))
STAGE1_MB=$(python3 -c "print(int(${STAGE1_BYTES} / 1024**2))")
STAGE2_MB=$(python3 -c "print(int(${STAGE2_BYTES} / 1024**2))")

echo "    Stage1: ${STAGE1_BYTES} bytes (${STAGE1_MB} MB) per task, ${N_TASKS} tasks"
echo "    Stage2: ${STAGE2_BYTES} bytes (${STAGE2_MB} MB) per task"

# ── Write Slurm job script ────────────────────────────────────────────────────
JOB_SCRIPT="${RESULTS_DIR}/job_storage_${STORAGE}.sh"
cat > "${JOB_SCRIPT}" << SLURM_EOF
#!/bin/bash
#SBATCH --job-name=dpm_${STORAGE}_${SIZE}_${NODES}n
#SBATCH --partition=${PARTITION}
#SBATCH --account=${ACCOUNT}
#SBATCH --nodes=${NODES}
#SBATCH --ntasks-per-node=${TASKS_PER_NODE}
#SBATCH --time=04:00:00
#SBATCH --output=${RESULTS_DIR}/slurm_%j.out
#SBATCH --error=${RESULTS_DIR}/slurm_%j.err

set -eo pipefail
source ${ROOT_DIR}/config.env
eval "\$(conda shell.bash hook)" 2>/dev/null || true
conda activate ${PYTHON_ENV} 2>/dev/null || source ${PYTHON_ENV}/bin/activate 2>/dev/null || true
set -u

# ── Node list ─────────────────────────────────────────────────────────────────
NODELIST=(\$(scontrol show hostnames \${SLURM_JOB_NODELIST}))
NUM_NODES=\${#NODELIST[@]}
echo "[run_storage] Nodes (\${NUM_NODES}): \${NODELIST[*]}"
echo "[run_storage] Tasks per node: ${TASKS_PER_NODE}, total tasks: ${N_TASKS}"

# Detect IOR
IOR_BIN=\$(which ior 2>/dev/null || echo "")
if [[ -z "\${IOR_BIN}" ]]; then
    echo "[run_storage] IOR not found — using dd fallback"
    USE_IOR=0
else
    echo "[run_storage] Using IOR: \${IOR_BIN}"
    USE_IOR=1
fi

WORK_DIR="${STORAGE_PATH}/dpm_eval_\${SLURM_JOB_ID}"
NODE_LOCAL=${NODE_LOCAL}
BEEGFS_AGG="${BEEGFS_PATH}/agg_tmp_\${SLURM_JOB_ID}"

# Create work dirs — on all nodes for node-local, once for shared
if [[ \${NODE_LOCAL} -eq 1 ]]; then
    for node in "\${NODELIST[@]}"; do
        srun --nodes=1 --ntasks=1 --nodelist="\${node}" mkdir -p "\${WORK_DIR}" &
    done
    wait
    mkdir -p "\${BEEGFS_AGG}"
else
    mkdir -p "\${WORK_DIR}"
fi

# Cleanup on all nodes
cleanup() {
    echo "[cleanup] removing work dirs"
    if [[ \${NODE_LOCAL} -eq 1 ]]; then
        for node in "\${NODELIST[@]}"; do
            srun --nodes=1 --ntasks=1 --nodelist="\${node}" rm -rf "\${WORK_DIR}" 2>/dev/null &
        done
        rm -rf "\${BEEGFS_AGG}" 2>/dev/null &
        wait
    else
        rm -rf "\${WORK_DIR}"
    fi
}
trap cleanup EXIT INT TERM

# Helper: get target node for task i
node_for_task() {
    echo "\${NODELIST[\$(( \$1 / ${TASKS_PER_NODE} ))]}"
}

# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: N parallel sim tasks — sequential write, 1MB transfer size
# Each task pinned to its assigned node via srun
# ─────────────────────────────────────────────────────────────────────────────
echo "=== Stage 1: Sim tasks (sequential write, 1MB xfer) ==="
T_STAGE1_START=\$(date +%s)

PIDS=()
for i in \$(seq 0 $((N_TASKS-1))); do
    TARGET_NODE=\$(node_for_task \${i})
    OUT_FILE="\${WORK_DIR}/sim_out_\${i}.bin"
    (
    echo "[task \${i}] node=\${TARGET_NODE}"
    if [[ \${USE_IOR} -eq 1 ]]; then
        srun --nodes=1 --ntasks=1 --nodelist="\${TARGET_NODE}" \
            ior -a POSIX -w -t 1m -b ${STAGE1_MB}m -o "\${OUT_FILE}" -F -k 2>&1
    else
        srun --nodes=1 --ntasks=1 --nodelist="\${TARGET_NODE}" \
            dd if=/dev/zero bs=1M count=${STAGE1_MB} of="\${OUT_FILE}" conv=fdatasync 2>&1
    fi
    ) > "${RESULTS_DIR}/stage1_\${i}.log" 2>&1 &
    PIDS+=(\$!)
done

STAGE1_FAILED=0
for pid in "\${PIDS[@]}"; do wait "\${pid}" || STAGE1_FAILED=\$((STAGE1_FAILED+1)); done
T_STAGE1_END=\$(date +%s)
STAGE1_TIME=\$((T_STAGE1_END - T_STAGE1_START))
echo "Stage 1 time: \${STAGE1_TIME}s (${N_TASKS} tasks, failed=\${STAGE1_FAILED})"

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: N parallel analysis tasks — seq read 1MB + seq write 1MB
# Each task pinned to its assigned node via srun
# ─────────────────────────────────────────────────────────────────────────────
echo "=== Stage 2: Analysis tasks (seq read 1MB + seq write 1MB) ==="
T_STAGE2_START=\$(date +%s)

PIDS=()
for i in \$(seq 0 $((N_TASKS-1))); do
    TARGET_NODE=\$(node_for_task \${i})
    IN_FILE="\${WORK_DIR}/sim_out_\${i}.bin"
    OUT_FILE="\${WORK_DIR}/analysis_out_\${i}.bin"
    (
    echo "[task \${i}] node=\${TARGET_NODE}"
    if [[ \${USE_IOR} -eq 1 ]]; then
        srun --nodes=1 --ntasks=1 --nodelist="\${TARGET_NODE}" \
            ior -a POSIX -r -t 1m -b ${STAGE2_MB}m -o "\${IN_FILE}" -F -k 2>&1
        srun --nodes=1 --ntasks=1 --nodelist="\${TARGET_NODE}" \
            ior -a POSIX -w -t 1m -b ${STAGE2_MB}m -o "\${OUT_FILE}" -F -k 2>&1
    else
        srun --nodes=1 --ntasks=1 --nodelist="\${TARGET_NODE}" bash -c \
            "dd if='\${IN_FILE}' of=/dev/null bs=1M 2>&1 && dd if=/dev/zero bs=1M count=${STAGE2_MB} of='\${OUT_FILE}' conv=fdatasync 2>&1"
    fi
    ) > "${RESULTS_DIR}/stage2_\${i}.log" 2>&1 &
    PIDS+=(\$!)
done

STAGE2_FAILED=0
for pid in "\${PIDS[@]}"; do wait "\${pid}" || STAGE2_FAILED=\$((STAGE2_FAILED+1)); done
T_STAGE2_END=\$(date +%s)
STAGE2_TIME=\$((T_STAGE2_END - T_STAGE2_START))
echo "Stage 2 time: \${STAGE2_TIME}s (failed=\${STAGE2_FAILED})"

# ─────────────────────────────────────────────────────────────────────────────
# Stage 3: Aggregate — for node-local storage, gather partials via BeeGFS
# ─────────────────────────────────────────────────────────────────────────────
echo "=== Stage 3: Aggregation (sequential read + write) ==="
T_STAGE3_START=\$(date +%s)

if [[ \${NODE_LOCAL} -eq 1 ]]; then
    # Phase A: each node concatenates its local analysis outputs to BeeGFS
    PIDS=()
    for node_idx in \$(seq 0 \$((NUM_NODES-1))); do
        TARGET_NODE=\${NODELIST[\$node_idx]}
        FIRST=\$((node_idx * ${TASKS_PER_NODE}))
        LAST=\$((FIRST + ${TASKS_PER_NODE} - 1))
        FILE_LIST=""
        for t in \$(seq \${FIRST} \${LAST}); do
            FILE_LIST="\${FILE_LIST} \${WORK_DIR}/analysis_out_\${t}.bin*"
        done
        srun --nodes=1 --ntasks=1 --nodelist="\${TARGET_NODE}" \
            bash -c "cat \${FILE_LIST} > \${BEEGFS_AGG}/partial_\${node_idx}.bin" &
        PIDS+=(\$!)
    done
    for pid in "\${PIDS[@]}"; do wait "\${pid}" || true; done
    # Phase B: combine partials on batch node
    cat "\${BEEGFS_AGG}"/partial_*.bin > "\${BEEGFS_AGG}/aggregate_out.bin" 2>&1 || true
else
    cat "\${WORK_DIR}"/analysis_out_*.bin* > "\${WORK_DIR}/aggregate_out.bin" 2>&1 || true
fi

T_STAGE3_END=\$(date +%s)
STAGE3_TIME=\$((T_STAGE3_END - T_STAGE3_START))
echo "Stage 3 time: \${STAGE3_TIME}s"

T_TOTAL=\$((T_STAGE3_END - T_STAGE1_START))
TOTAL_FAILED=\$((STAGE1_FAILED + STAGE2_FAILED))
STATUS=\$([ \${TOTAL_FAILED} -eq 0 ] && echo "SUCCESS" || echo "FAILED")

{
echo "RESULT: size=${SIZE}, backend=${STORAGE}, nodes=${NODES}"
echo "stage1_time_s=\${STAGE1_TIME}"
echo "stage2_time_s=\${STAGE2_TIME}"
echo "stage3_time_s=\${STAGE3_TIME}"
echo "total_time_s=\${T_TOTAL}"
echo "failed_tasks=\${TOTAL_FAILED}"
echo "status=\${STATUS}"
echo "ior_used=\${USE_IOR}"
echo "nodelist=\${NODELIST[*]}"
echo "multinode=true"
} > "${RESULTS_DIR}/result.txt"
cat "${RESULTS_DIR}/result.txt"
SLURM_EOF

echo "Submitting: sbatch ${JOB_SCRIPT}"
sbatch "${JOB_SCRIPT}"
echo "Monitor: tail -f ${RESULTS_DIR}/slurm_*.out"
