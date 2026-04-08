#!/bin/bash
# run_adios_sst.sh — Run the synthetic workflow using ADIOS2 SST engine
#
# This is the BASELINE for comparison with DPM.
# Expected: succeeds on small, degrades on medium, fails (OOM/timeout) on large.
#
# Usage:
#   bash scripts/run_adios_sst.sh --size small  --nodes 4
#   bash scripts/run_adios_sst.sh --size large  --nodes 4

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
RUN_ID="adios_sst_${SIZE}_${NODES}n_${TIMESTAMP}"
RESULTS_DIR="${ROOT_DIR}/results/${RUN_ID}"
mkdir -p "${RESULTS_DIR}"

echo "=== ADIOS SST run: size=${SIZE}, nodes=${NODES} ==="
echo "    Results: ${RESULTS_DIR}"

# ── Extract data size from workflow JSON ──────────────────────────────────────
WORKFLOW_JSON="${ROOT_DIR}/wfbench/workflow_${SIZE}_${NODES}n.json"
# Fallback to non-node-count JSON if per-node-count JSON not generated yet
if [[ ! -f "${WORKFLOW_JSON}" ]]; then
    WORKFLOW_JSON="${ROOT_DIR}/wfbench/workflow_${SIZE}.json"
fi
if [[ ! -f "${WORKFLOW_JSON}" ]]; then
    echo "ERROR: workflow JSON not found. Run: python wfbench/generate_workflow.py --size ${SIZE} --nodes ${NODES}"
    exit 1
fi

STAGE1_BYTES=$(python3 -c "
import json, sys
wf = json.load(open('${WORKFLOW_JSON}'))
print(wf['dpmMeta']['stage1FileSizeBytes'])
")
STAGE1_GB=$(python3 -c "print(${STAGE1_BYTES} / 1024**3)")
N_TASKS=$(python3 -c "
import json
wf = json.load(open('${WORKFLOW_JSON}'))
print(sum(1 for t in wf['workflow']['specification']['tasks'] if t['category']=='sim'))
")

echo "    Stage1 file size: ${STAGE1_GB} GB per task, ${N_TASKS} tasks"

# ── Write Slurm job script ────────────────────────────────────────────────────
JOB_SCRIPT="${RESULTS_DIR}/job_adios_sst.sh"
cat > "${JOB_SCRIPT}" << SLURM_EOF
#!/bin/bash
#SBATCH --job-name=adios_sst_${SIZE}
#SBATCH --partition=${PARTITION}
#SBATCH --account=${ACCOUNT}
#SBATCH --nodes=${NODES}
#SBATCH --ntasks-per-node=${CORES_PER_NODE}
#SBATCH --time=02:00:00
#SBATCH --output=${RESULTS_DIR}/slurm_%j.out
#SBATCH --error=${RESULTS_DIR}/slurm_%j.err

source ${ROOT_DIR}/config.env
eval "\$(conda shell.bash hook)" 2>/dev/null || true
conda activate ${PYTHON_ENV} 2>/dev/null || source ${PYTHON_ENV}/bin/activate 2>/dev/null || true
export PATH="${PYTHON_ENV}/bin:\${PATH}"
export PYTHONUNBUFFERED=1
module load ${ADIOS2_MODULE} 2>/dev/null || true

export ADIOS2_CONFIG_FILE="${ROOT_DIR}/adios/adios2.xml"

# Rendezvous directory (must be on shared filesystem, visible to all nodes)
RENDEZVOUS_DIR="${BEEGFS_PATH}/adios_rendezvous_\${SLURM_JOB_ID}"
mkdir -p "\${RENDEZVOUS_DIR}"

# Cleanup on exit, timeout, or kill — removes rendezvous dir AND consumer .bp outputs
cleanup() {
    echo "[cleanup] removing \${RENDEZVOUS_DIR} and analysis_out_*.bp"
    rm -rf "\${RENDEZVOUS_DIR}"
    rm -rf "${BEEGFS_PATH}"/analysis_out_*.bp
}
trap cleanup EXIT ERR INT TERM

echo "=== Launching producer-consumer pairs (ADIOS SST) ==="
T_STAGE1_START=\$(date +%s)

# Launch each producer-consumer pair with staggering:
# 1. Start producer (it creates .sst rendezvous file)
# 2. Wait for .sst file to appear (confirms producer is ready)
# 3. Start consumer (connects via .sst file)
# This avoids the race condition where consumers start before producers are ready.
PRODUCER_PIDS=()
CONSUMER_PIDS=()
for i in \$(seq 0 $((N_TASKS-1))); do
    SST_FILE="\${RENDEZVOUS_DIR}/sim_out_\${i}.sst"

    # Launch producer
    python3 ${ROOT_DIR}/adios/producer_task.py \
        --output-name "\${RENDEZVOUS_DIR}/sim_out_\${i}" \
        --data-size-gb ${STAGE1_GB} \
        --transfer-size-mb 1 \
        > "${RESULTS_DIR}/producer_\${i}.log" 2>&1 &
    PRODUCER_PIDS+=(\$!)

    # Wait for SST rendezvous file (up to 30s)
    WAITED=0
    while [[ ! -f "\${SST_FILE}" ]] && [[ \${WAITED} -lt 30 ]]; do
        sleep 0.5
        WAITED=\$((WAITED+1))
    done
    if [[ ! -f "\${SST_FILE}" ]]; then
        echo "WARNING: SST file \${SST_FILE} not created after 15s"
    fi

    # Launch consumer
    python3 ${ROOT_DIR}/adios/consumer_task.py \
        --input-name "\${RENDEZVOUS_DIR}/sim_out_\${i}" \
        --output-path "\${BEEGFS_PATH}/analysis_out_\${i}.bp" \
        > "${RESULTS_DIR}/consumer_\${i}.log" 2>&1 &
    CONSUMER_PIDS+=(\$!)

    echo "  Pair \${i}: producer PID=\${PRODUCER_PIDS[-1]}, consumer PID=\${CONSUMER_PIDS[-1]}"
done
echo "All ${N_TASKS} pairs launched"

# Wait for all and collect exit codes
FAILED=0
for pid in "\${PRODUCER_PIDS[@]}"; do
    wait "\${pid}" || FAILED=\$((FAILED+1))
done
for pid in "\${CONSUMER_PIDS[@]}"; do
    wait "\${pid}" || FAILED=\$((FAILED+1))
done

T_END=\$(date +%s)
# Stage 1 and 2 ran simultaneously — report combined as stage1, 0 for stage2, stage3
STAGE1_TIME=\$((T_END - T_STAGE1_START))
STAGE2_TIME=0   # overlapped with stage1 in SST mode
STAGE3_TIME=0   # no stage3 in ADIOS SST run
TOTAL_TIME=\$((T_END - T_STAGE1_START))

{
echo "RESULT: size=${SIZE}, backend=adios_sst, nodes=${NODES}"
echo "stage1_time_s=\${STAGE1_TIME}"
echo "stage2_time_s=\${STAGE2_TIME}"
echo "stage3_time_s=\${STAGE3_TIME}"
echo "total_time_s=\${TOTAL_TIME}"
echo "failed_tasks=\${FAILED}"
echo "status=\$([ \${FAILED} -eq 0 ] && echo SUCCESS || echo FAILED)"
} >> "${RESULTS_DIR}/result.txt"

cat "${RESULTS_DIR}/result.txt"

# Cleanup handled by trap — no explicit rm needed here
SLURM_EOF

echo "Submitting: sbatch ${JOB_SCRIPT}"
sbatch "${JOB_SCRIPT}"
echo "Monitor: tail -f ${RESULTS_DIR}/slurm_*.out"
