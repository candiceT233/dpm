#!/bin/bash
# run_dpm_mixed.sh — Run the synthetic workflow using DPM-recommended mixed storage
#
# DPM analysis recommends:
#   Stage 1 (sequential write 1MB): BeeGFS  — high bandwidth, shared across nodes
#   Stage 2 (sequential read 1MB + sequential write 1MB): SSD — fast local I/O
#   Stage 3 (sequential read aggregation): SSD — data already local from Stage 2
#
# A staging step copies Stage 1 output from BeeGFS → per-node SSD,
# simulating DPM's data placement decision. Each node copies its own files.
#
# Tasks are distributed across all allocated nodes via srun.
#
# Usage:
#   bash scripts/run_dpm_mixed.sh --size small  --nodes 4
#   bash scripts/run_dpm_mixed.sh --size large  --nodes 32

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"
source "${ROOT_DIR}/config.env"

# ── Parse arguments ───────────────────────────────────────────────────────────
SIZE="small"
NODES="${NODES:-4}"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --size)   SIZE="$2";  shift 2 ;;
        --nodes)  NODES="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUN_ID="dpm_mixed_${SIZE}_${NODES}n_${TIMESTAMP}"
RESULTS_DIR="${ROOT_DIR}/results/${RUN_ID}"
mkdir -p "${RESULTS_DIR}"

echo "=== DPM mixed-storage run: size=${SIZE}, nodes=${NODES} ==="
echo "    Stage 1 storage: BeeGFS (${BEEGFS_PATH}) — sequential write"
echo "    Staging: BeeGFS → per-node SSD"
echo "    Stage 2 storage: SSD (${LOCAL_SSD_PATH}) — seq read + write"
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
JOB_SCRIPT="${RESULTS_DIR}/job_dpm_mixed.sh"
cat > "${JOB_SCRIPT}" << SLURM_EOF
#!/bin/bash
#SBATCH --job-name=dpm_mixed_${SIZE}_${NODES}n
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
echo "[dpm_mixed] Nodes (\${NUM_NODES}): \${NODELIST[*]}"
echo "[dpm_mixed] Tasks per node: ${TASKS_PER_NODE}, total tasks: ${N_TASKS}"

# Detect IOR
IOR_BIN=\$(which ior 2>/dev/null || echo "")
if [[ -z "\${IOR_BIN}" ]]; then
    echo "[dpm_mixed] IOR not found — using dd fallback"
    USE_IOR=0
else
    echo "[dpm_mixed] Using IOR: \${IOR_BIN}"
    USE_IOR=1
fi

# Two work directories: BeeGFS for Stage 1, per-node SSD for Stage 2+3
BEEGFS_WORK="${BEEGFS_PATH}/dpm_eval_\${SLURM_JOB_ID}"
SSD_WORK="${LOCAL_SSD_PATH}/dpm_eval_\${SLURM_JOB_ID}"
BEEGFS_AGG="${BEEGFS_PATH}/agg_tmp_\${SLURM_JOB_ID}"

mkdir -p "\${BEEGFS_WORK}" "\${BEEGFS_AGG}"
# Create SSD work dir on each node
for node in "\${NODELIST[@]}"; do
    srun --nodes=1 --ntasks=1 --nodelist="\${node}" mkdir -p "\${SSD_WORK}" &
done
wait

# Cleanup all locations on all nodes
cleanup() {
    echo "[cleanup] removing work dirs"
    rm -rf "\${BEEGFS_WORK}" "\${BEEGFS_AGG}" 2>/dev/null &
    for node in "\${NODELIST[@]}"; do
        srun --nodes=1 --ntasks=1 --nodelist="\${node}" rm -rf "\${SSD_WORK}" 2>/dev/null &
    done
    wait
}
trap cleanup EXIT INT TERM

# Helper: get target node for task i
node_for_task() {
    echo "\${NODELIST[\$(( \$1 / ${TASKS_PER_NODE} ))]}"
}

# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: N parallel sim tasks — sequential write 1MB → BeeGFS
# Each task pinned to its assigned node, writing to shared BeeGFS
# ─────────────────────────────────────────────────────────────────────────────
echo "=== Stage 1: Sim tasks (sequential write 1MB → BeeGFS) ==="
T_STAGE1_START=\$(date +%s)

PIDS=()
for i in \$(seq 0 $((N_TASKS-1))); do
    TARGET_NODE=\$(node_for_task \${i})
    OUT_FILE="\${BEEGFS_WORK}/sim_out_\${i}.bin"
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
# Staging: Copy Stage 1 output from BeeGFS → per-node SSD
# Each task's cp runs on its target node, reading BeeGFS (network), writing local SSD
# ─────────────────────────────────────────────────────────────────────────────
echo "=== Staging: BeeGFS → per-node SSD (DPM data placement) ==="
T_STAGING_START=\$(date +%s)

PIDS=()
for i in \$(seq 0 $((N_TASKS-1))); do
    TARGET_NODE=\$(node_for_task \${i})
    SRC="\${BEEGFS_WORK}/sim_out_\${i}.bin"
    DST="\${SSD_WORK}/sim_out_\${i}.bin"
    if [[ \${USE_IOR} -eq 1 ]]; then
        SRC="\${SRC}.00000000"
        DST="\${DST}.00000000"
    fi
    srun --nodes=1 --ntasks=1 --nodelist="\${TARGET_NODE}" \
        cp "\${SRC}" "\${DST}" &
    PIDS+=(\$!)
done
for pid in "\${PIDS[@]}"; do wait "\${pid}"; done

T_STAGING_END=\$(date +%s)
STAGING_TIME=\$((T_STAGING_END - T_STAGING_START))
echo "Staging time: \${STAGING_TIME}s (copied ${N_TASKS} files BeeGFS → per-node SSD)"

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: N parallel analysis tasks — seq read 1MB + seq write 1MB → SSD
# Each task runs on its assigned node, reading/writing node-local SSD
# ─────────────────────────────────────────────────────────────────────────────
echo "=== Stage 2: Analysis tasks (seq read 1MB + seq write 1MB → SSD) ==="
T_STAGE2_START=\$(date +%s)

PIDS=()
for i in \$(seq 0 $((N_TASKS-1))); do
    TARGET_NODE=\$(node_for_task \${i})
    IN_FILE="\${SSD_WORK}/sim_out_\${i}.bin"
    OUT_FILE="\${SSD_WORK}/analysis_out_\${i}.bin"
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
# Stage 3: Aggregate — gather per-node SSD partials via BeeGFS
# ─────────────────────────────────────────────────────────────────────────────
echo "=== Stage 3: Aggregation (gather from per-node SSD via BeeGFS) ==="
T_STAGE3_START=\$(date +%s)

# Phase A: each node concatenates its local outputs to BeeGFS
PIDS=()
for node_idx in \$(seq 0 \$((NUM_NODES-1))); do
    TARGET_NODE=\${NODELIST[\$node_idx]}
    FIRST=\$((node_idx * ${TASKS_PER_NODE}))
    LAST=\$((FIRST + ${TASKS_PER_NODE} - 1))
    FILE_LIST=""
    for t in \$(seq \${FIRST} \${LAST}); do
        FILE_LIST="\${FILE_LIST} \${SSD_WORK}/analysis_out_\${t}.bin*"
    done
    srun --nodes=1 --ntasks=1 --nodelist="\${TARGET_NODE}" \
        bash -c "cat \${FILE_LIST} > \${BEEGFS_AGG}/partial_\${node_idx}.bin" &
    PIDS+=(\$!)
done
for pid in "\${PIDS[@]}"; do wait "\${pid}" || true; done
# Phase B: combine partials
cat "\${BEEGFS_AGG}"/partial_*.bin > "\${BEEGFS_AGG}/aggregate_out.bin" 2>&1 || true

T_STAGE3_END=\$(date +%s)
STAGE3_TIME=\$((T_STAGE3_END - T_STAGE3_START))
echo "Stage 3 time: \${STAGE3_TIME}s"

T_TOTAL=\$((T_STAGE3_END - T_STAGE1_START))
TOTAL_FAILED=\$((STAGE1_FAILED + STAGE2_FAILED))
STATUS=\$([ \${TOTAL_FAILED} -eq 0 ] && echo "SUCCESS" || echo "FAILED")

{
echo "RESULT: size=${SIZE}, backend=dpm_mixed, nodes=${NODES}"
echo "stage1_time_s=\${STAGE1_TIME}"
echo "staging_time_s=\${STAGING_TIME}"
echo "stage2_time_s=\${STAGE2_TIME}"
echo "stage3_time_s=\${STAGE3_TIME}"
echo "total_time_s=\${T_TOTAL}"
echo "failed_tasks=\${TOTAL_FAILED}"
echo "status=\${STATUS}"
echo "ior_used=\${USE_IOR}"
echo "stage1_storage=beegfs"
echo "staging=beegfs_to_per_node_ssd"
echo "stage2_storage=ssd"
echo "stage3_storage=ssd_to_beegfs_agg"
echo "nodelist=\${NODELIST[*]}"
echo "multinode=true"
} > "${RESULTS_DIR}/result.txt"
cat "${RESULTS_DIR}/result.txt"
SLURM_EOF

echo "Submitting: sbatch ${JOB_SCRIPT}"
sbatch "${JOB_SCRIPT}"
echo "Monitor: tail -f ${RESULTS_DIR}/slurm_*.out"
