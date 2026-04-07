#!/bin/bash
# run_storage.sh — Run the synthetic workflow using file-based storage (DPM config)
#
# Uses IOR for I/O operations with the SAME transfer-size parameters that DPM
# profiled (sw 1MB for stage1, rr 4KB for stage2, sr 1MB for stage3), so that
# DPM score predictions are directly comparable to measured times.
#
# Falls back to Python I/O script if IOR is not available on the cluster.
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

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUN_ID="${STORAGE}_${SIZE}_${NODES}n_${TIMESTAMP}"
RESULTS_DIR="${ROOT_DIR}/results/${RUN_ID}"
mkdir -p "${RESULTS_DIR}"

echo "=== Storage run: size=${SIZE}, storage=${STORAGE}, nodes=${NODES} ==="
echo "    Storage path: ${STORAGE_PATH}"
echo "    Results: ${RESULTS_DIR}"

# ── Extract metadata from workflow JSON ───────────────────────────────────────
WORKFLOW_JSON="${ROOT_DIR}/wfbench/workflow_${SIZE}_${NODES}n.json"
# Fallback to 4-node JSON if per-node-count JSON not generated yet
if [[ ! -f "${WORKFLOW_JSON}" ]]; then
    WORKFLOW_JSON="${ROOT_DIR}/wfbench/workflow_${SIZE}.json"
fi
if [[ ! -f "${WORKFLOW_JSON}" ]]; then
    echo "ERROR: ${WORKFLOW_JSON} not found."
    echo "Run: python wfbench/generate_workflow.py --size ${SIZE} --nodes ${NODES} --mem-per-node \${MEM_PER_NODE_GB}"
    exit 1
fi

STAGE1_BYTES=$(python3 -c "import json; wf=json.load(open('${WORKFLOW_JSON}')); print(wf['dpmMeta']['stage1FileSizeBytes'])")
STAGE2_BYTES=$(python3 -c "import json; wf=json.load(open('${WORKFLOW_JSON}')); print(wf['dpmMeta']['stage2FileSizeBytes'])")
N_TASKS=$(python3 -c "import json; wf=json.load(open('${WORKFLOW_JSON}')); print(sum(1 for t in wf['workflow']['specification']['tasks'] if t['category']=='sim'))")

# For phase 3 scaling: N_TASKS from the JSON may not match NODES if JSON was 4-node
# Override N_TASKS based on actual NODES × TASKS_PER_NODE
N_TASKS=$((NODES * TASKS_PER_NODE))

echo "    Stage1: ${STAGE1_BYTES} bytes per task, ${N_TASKS} tasks"
echo "    Stage2: ${STAGE2_BYTES} bytes per task (1/8 reduction)"

# ── Write Slurm job script ────────────────────────────────────────────────────
JOB_SCRIPT="${RESULTS_DIR}/job_storage_${STORAGE}.sh"
cat > "${JOB_SCRIPT}" << SLURM_EOF
#!/bin/bash
#SBATCH --job-name=dpm_${STORAGE}_${SIZE}_${NODES}n
#SBATCH --partition=${PARTITION}
#SBATCH --account=${ACCOUNT}
#SBATCH --nodes=${NODES}
#SBATCH --ntasks-per-node=${CORES_PER_NODE}
#SBATCH --time=04:00:00
#SBATCH --output=${RESULTS_DIR}/slurm_%j.out
#SBATCH --error=${RESULTS_DIR}/slurm_%j.err

source ${ROOT_DIR}/config.env
source ${PYTHON_ENV}/bin/activate 2>/dev/null || true
module load ${ADIOS2_MODULE} 2>/dev/null || true

# Detect IOR — use it if available, else fall back to Python I/O script
IOR_BIN=\$(which ior 2>/dev/null || echo "")
if [[ -z "\${IOR_BIN}" ]]; then
    echo "[run_storage] IOR not found — using Python fallback for I/O patterns"
    USE_IOR=0
else
    echo "[run_storage] Using IOR: \${IOR_BIN}"
    USE_IOR=1
fi

WORK_DIR="${STORAGE_PATH}/dpm_eval_\${SLURM_JOB_ID}"
mkdir -p "\${WORK_DIR}"

# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: N parallel sim tasks — sequential write, 1MB transfer size
# (matches DPM IOR profiling pattern: ior -a POSIX -w -t 1m)
# ─────────────────────────────────────────────────────────────────────────────
echo "=== Stage 1: Sim tasks (sequential write, 1MB xfer) ==="
T_STAGE1_START=\$(date +%s)

PIDS=()
for i in \$(seq 0 $((N_TASKS-1))); do
    OUT_FILE="\${WORK_DIR}/sim_out_\${i}.bin"
    STAGE1_MB=\$(python3 -c "print(int(${STAGE1_BYTES} / 1024**2))")
    (
    if [[ \${USE_IOR} -eq 1 ]]; then
        # IOR sequential write, 1MB transfer — same pattern DPM profiled
        ior -a POSIX -w -t 1m -b \${STAGE1_MB}m -o "\${OUT_FILE}" \
            -F -k -q 2>&1
    else
        # Python fallback: sequential write in 1MB chunks
        python3 - <<'PYEOF'
import sys, os
out = "${OUT_FILE}"
size = ${STAGE1_BYTES}
chunk = 1024 * 1024  # 1MB
buf = b'\x00' * chunk
written = 0
with open(out, 'wb') as f:
    while written < size:
        n = min(chunk, size - written)
        f.write(buf[:n])
        written += n
    f.flush()
    os.fsync(f.fileno())
print(f"[sim_{i}] wrote {written/(1024**3):.2f} GB to {out}")
PYEOF
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
# Stage 2: N parallel analysis tasks — random read 4KB, then sequential write 1MB
# (matches DPM IOR profiling pattern: ior -a POSIX -r -z -t 4k / -w -t 1m)
# ─────────────────────────────────────────────────────────────────────────────
echo "=== Stage 2: Analysis tasks (random read 4KB + seq write) ==="
T_STAGE2_START=\$(date +%s)

PIDS=()
for i in \$(seq 0 $((N_TASKS-1))); do
    IN_FILE="\${WORK_DIR}/sim_out_\${i}.bin"
    OUT_FILE="\${WORK_DIR}/analysis_out_\${i}.bin"
    STAGE2_MB=\$(python3 -c "print(int(${STAGE2_BYTES} / 1024**2))")
    (
    if [[ \${USE_IOR} -eq 1 ]]; then
        # IOR random read with 4KB transfer — same pattern DPM profiled
        ior -a POSIX -r -z -t 4k -b \${STAGE2_MB}m -o "\${IN_FILE}" \
            -F -k -q 2>&1
        # Sequential write of reduced output
        ior -a POSIX -w -t 1m -b \${STAGE2_MB}m -o "\${OUT_FILE}" \
            -F -k -q 2>&1
    else
        # Python fallback: random read in 4KB chunks, sequential write
        python3 - <<'PYEOF'
import sys, os, random
in_f = "${IN_FILE}"
out_f = "${OUT_FILE}"
in_size = ${STAGE1_BYTES}
out_size = ${STAGE2_BYTES}
chunk_r = 4096          # 4KB random read
chunk_w = 1024 * 1024   # 1MB sequential write
n_reads = in_size // chunk_r
buf_w = b'\x00' * chunk_w
written = 0
with open(in_f, 'rb') as fin, open(out_f, 'wb') as fout:
    for _ in range(n_reads):
        offset = random.randint(0, max(0, in_size - chunk_r))
        fin.seek(offset)
        fin.read(chunk_r)
    while written < out_size:
        n = min(chunk_w, out_size - written)
        fout.write(buf_w[:n])
        written += n
    fout.flush()
    os.fsync(fout.fileno())
print(f"[analysis_{i}] random-read {n_reads} x 4KB, wrote {written/(1024**2):.1f} MB")
PYEOF
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
# Stage 3: Aggregate — sequential read all analysis outputs, write summary
# ─────────────────────────────────────────────────────────────────────────────
echo "=== Stage 3: Aggregation (sequential read + write) ==="
T_STAGE3_START=\$(date +%s)
cat "\${WORK_DIR}"/analysis_out_*.bin > "\${WORK_DIR}/aggregate_out.bin" 2>&1 || true
T_STAGE3_END=\$(date +%s)
STAGE3_TIME=\$((T_STAGE3_END - T_STAGE3_START))
echo "Stage 3 time: \${STAGE3_TIME}s"

T_TOTAL=\$((T_STAGE3_END - T_STAGE1_START))
TOTAL_FAILED=\$((STAGE1_FAILED + STAGE2_FAILED))
STATUS=\$([ \${TOTAL_FAILED} -eq 0 ] && echo "SUCCESS" || echo "FAILED")

# Write result.txt in format collect_results.sh expects
{
echo "RESULT: size=${SIZE}, backend=${STORAGE}, nodes=${NODES}"
echo "stage1_time_s=\${STAGE1_TIME}"
echo "stage2_time_s=\${STAGE2_TIME}"
echo "stage3_time_s=\${STAGE3_TIME}"
echo "total_time_s=\${T_TOTAL}"
echo "failed_tasks=\${TOTAL_FAILED}"
echo "status=\${STATUS}"
echo "ior_used=\${USE_IOR}"
} > "${RESULTS_DIR}/result.txt"
cat "${RESULTS_DIR}/result.txt"

# Cleanup work directory
rm -rf "\${WORK_DIR}"
SLURM_EOF

echo "Submitting: sbatch ${JOB_SCRIPT}"
sbatch "${JOB_SCRIPT}"
echo "Monitor: tail -f ${RESULTS_DIR}/slurm_*.out"
