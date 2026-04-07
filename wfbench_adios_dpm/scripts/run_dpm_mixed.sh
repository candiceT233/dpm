#!/bin/bash
# run_dpm_mixed.sh — Run the synthetic workflow using DPM-recommended mixed storage
#
# DPM analysis recommends:
#   Stage 1 (sequential write 1MB): BeeGFS  — high bandwidth, shared across nodes
#   Stage 2 (random read 4KB + sequential write 1MB): SSD — low latency random I/O
#   Stage 3 (sequential read aggregation): SSD — data already local from Stage 2
#
# This represents what DPM would select based on I/O pattern profiling:
#   - BeeGFS excels at large sequential I/O but is terrible for small random reads
#   - Node-local NVMe SSD handles both patterns well, especially random 4KB reads
#
# A staging step copies Stage 1 output from BeeGFS → SSD between stages,
# simulating DPM's data placement decision.
#
# Usage:
#   bash scripts/run_dpm_mixed.sh --size small  --nodes 4
#   bash scripts/run_dpm_mixed.sh --size large  --nodes 4
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
echo "    Stage 2 storage: SSD (${LOCAL_SSD_PATH}) — random read + write"
echo "    Results: ${RESULTS_DIR}"

# ── Extract metadata from workflow JSON ───────────────────────────────────────
WORKFLOW_JSON="${ROOT_DIR}/wfbench/workflow_${SIZE}_${NODES}n.json"
if [[ ! -f "${WORKFLOW_JSON}" ]]; then
    WORKFLOW_JSON="${ROOT_DIR}/wfbench/workflow_${SIZE}.json"
fi
if [[ ! -f "${WORKFLOW_JSON}" ]]; then
    echo "ERROR: ${WORKFLOW_JSON} not found."
    echo "Run: python wfbench/generate_workflow.py --size ${SIZE} --nodes ${NODES}"
    exit 1
fi

STAGE1_BYTES=$(python3 -c "import json; wf=json.load(open('${WORKFLOW_JSON}')); print(wf['dpmMeta']['stage1FileSizeBytes'])")
STAGE2_BYTES=$(python3 -c "import json; wf=json.load(open('${WORKFLOW_JSON}')); print(wf['dpmMeta']['stage2FileSizeBytes'])")
N_TASKS=$((NODES * TASKS_PER_NODE))

echo "    Stage1: ${STAGE1_BYTES} bytes per task, ${N_TASKS} tasks"
echo "    Stage2: ${STAGE2_BYTES} bytes per task (1/8 reduction)"

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

source ${ROOT_DIR}/config.env
eval "\$(conda shell.bash hook)" 2>/dev/null || true
conda activate ${PYTHON_ENV} 2>/dev/null || source ${PYTHON_ENV}/bin/activate 2>/dev/null || true
module load ${ADIOS2_MODULE} 2>/dev/null || true

# Detect IOR
IOR_BIN=\$(which ior 2>/dev/null || echo "")
if [[ -z "\${IOR_BIN}" ]]; then
    echo "[dpm_mixed] IOR not found — using Python fallback"
    USE_IOR=0
else
    echo "[dpm_mixed] Using IOR: \${IOR_BIN}"
    USE_IOR=1
fi

# Two work directories: BeeGFS for Stage 1, SSD for Stage 2+3
BEEGFS_WORK="${BEEGFS_PATH}/dpm_eval_\${SLURM_JOB_ID}"
SSD_WORK="${LOCAL_SSD_PATH}/dpm_eval_\${SLURM_JOB_ID}"
mkdir -p "\${BEEGFS_WORK}"
mkdir -p "\${SSD_WORK}"

# Cleanup both on exit/kill
cleanup() {
    echo "[cleanup] removing \${BEEGFS_WORK} and \${SSD_WORK}"
    rm -rf "\${BEEGFS_WORK}" "\${SSD_WORK}"
}
trap cleanup EXIT INT TERM

# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: N parallel sim tasks — sequential write 1MB → BeeGFS
# DPM rationale: BeeGFS has high sequential write bandwidth across nodes
# ─────────────────────────────────────────────────────────────────────────────
echo "=== Stage 1: Sim tasks (sequential write 1MB → BeeGFS) ==="
T_STAGE1_START=\$(date +%s)

PIDS=()
for i in \$(seq 0 $((N_TASKS-1))); do
    OUT_FILE="\${BEEGFS_WORK}/sim_out_\${i}.bin"
    STAGE1_MB=\$(python3 -c "print(int(${STAGE1_BYTES} / 1024**2))")
    (
    if [[ \${USE_IOR} -eq 1 ]]; then
        ior -a POSIX -w -t 1m -b \${STAGE1_MB}m -o "\${OUT_FILE}" -F -k 2>&1
    else
        export PY_OUT_FILE="\${OUT_FILE}" PY_SIZE=${STAGE1_BYTES} PY_TASK="\${i}"
        python3 - <<'PYEOF'
import sys, os
out = os.environ["PY_OUT_FILE"]
size = int(os.environ["PY_SIZE"])
task = os.environ["PY_TASK"]
chunk = 1024 * 1024
buf = b'\x00' * chunk
written = 0
with open(out, 'wb') as f:
    while written < size:
        n = min(chunk, size - written)
        f.write(buf[:n])
        written += n
    f.flush()
    os.fsync(f.fileno())
print(f"[sim_{task}] wrote {written/(1024**3):.2f} GB to {out}")
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
# Staging: Copy Stage 1 output from BeeGFS → SSD (DPM data placement)
# This is the cost of DPM's storage selection — moving data to the optimal tier
# ─────────────────────────────────────────────────────────────────────────────
echo "=== Staging: BeeGFS → SSD (DPM data placement) ==="
T_STAGING_START=\$(date +%s)

PIDS=()
for i in \$(seq 0 $((N_TASKS-1))); do
    # IOR with -F creates files with .00000000 suffix; Python fallback uses plain name
    SRC="\${BEEGFS_WORK}/sim_out_\${i}.bin"
    if [[ \${USE_IOR} -eq 1 ]]; then
        SRC="\${SRC}.00000000"
    fi
    DST="\${SSD_WORK}/sim_out_\${i}.bin"
    if [[ \${USE_IOR} -eq 1 ]]; then
        DST="\${DST}.00000000"
    fi
    cp "\${SRC}" "\${DST}" &
    PIDS+=(\$!)
done
for pid in "\${PIDS[@]}"; do wait "\${pid}"; done

T_STAGING_END=\$(date +%s)
STAGING_TIME=\$((T_STAGING_END - T_STAGING_START))
echo "Staging time: \${STAGING_TIME}s (copied ${N_TASKS} files BeeGFS → SSD)"

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: N parallel analysis tasks — random read 4KB + seq write 1MB → SSD
# DPM rationale: SSD has low-latency random I/O, unlike BeeGFS
# ─────────────────────────────────────────────────────────────────────────────
echo "=== Stage 2: Analysis tasks (random read 4KB + seq write → SSD) ==="
T_STAGE2_START=\$(date +%s)

PIDS=()
for i in \$(seq 0 $((N_TASKS-1))); do
    IN_FILE="\${SSD_WORK}/sim_out_\${i}.bin"
    OUT_FILE="\${SSD_WORK}/analysis_out_\${i}.bin"
    STAGE2_MB=\$(python3 -c "print(int(${STAGE2_BYTES} / 1024**2))")
    (
    if [[ \${USE_IOR} -eq 1 ]]; then
        ior -a POSIX -r -z -t 4k -b \${STAGE2_MB}m -o "\${IN_FILE}" -F -k 2>&1
        ior -a POSIX -w -t 1m -b \${STAGE2_MB}m -o "\${OUT_FILE}" -F -k 2>&1
    else
        export PY_IN_FILE="\${IN_FILE}" PY_OUT_FILE="\${OUT_FILE}" PY_IN_SIZE=${STAGE1_BYTES} PY_OUT_SIZE=${STAGE2_BYTES} PY_TASK="\${i}"
        python3 - <<'PYEOF'
import sys, os, random
in_f = os.environ["PY_IN_FILE"]
out_f = os.environ["PY_OUT_FILE"]
in_size = int(os.environ["PY_IN_SIZE"])
out_size = int(os.environ["PY_OUT_SIZE"])
task = os.environ["PY_TASK"]
chunk_r = 4096
chunk_w = 1024 * 1024
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
print(f"[analysis_{task}] random-read {n_reads} x 4KB, wrote {written/(1024**2):.1f} MB")
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
# Stage 3: Aggregate — sequential read all Stage 2 outputs from SSD
# ─────────────────────────────────────────────────────────────────────────────
echo "=== Stage 3: Aggregation (sequential read from SSD) ==="
T_STAGE3_START=\$(date +%s)
cat "\${SSD_WORK}"/analysis_out_*.bin* > "\${SSD_WORK}/aggregate_out.bin" 2>&1 || true
T_STAGE3_END=\$(date +%s)
STAGE3_TIME=\$((T_STAGE3_END - T_STAGE3_START))
echo "Stage 3 time: \${STAGE3_TIME}s"

T_TOTAL=\$((T_STAGE3_END - T_STAGE1_START))
TOTAL_FAILED=\$((STAGE1_FAILED + STAGE2_FAILED))
STATUS=\$([ \${TOTAL_FAILED} -eq 0 ] && echo "SUCCESS" || echo "FAILED")

# Write result.txt
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
echo "stage2_storage=ssd"
echo "stage3_storage=ssd"
} > "${RESULTS_DIR}/result.txt"
cat "${RESULTS_DIR}/result.txt"

# Cleanup handled by trap
SLURM_EOF

echo "Submitting: sbatch ${JOB_SCRIPT}"
sbatch "${JOB_SCRIPT}"
echo "Monitor: tail -f ${RESULTS_DIR}/slurm_*.out"
