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
WORKFLOW_JSON="${ROOT_DIR}/wfbench/workflow_${SIZE}.json"
if [[ ! -f "${WORKFLOW_JSON}" ]]; then
    echo "ERROR: ${WORKFLOW_JSON} not found. Run: python wfbench/generate_workflow.py --size ${SIZE}"
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
#SBATCH --nodes=${NODES}
#SBATCH --ntasks-per-node=${CORES_PER_NODE}
#SBATCH --time=02:00:00
#SBATCH --output=${RESULTS_DIR}/slurm_%j.out
#SBATCH --error=${RESULTS_DIR}/slurm_%j.err
# TODO: add account, reservation, or other cluster-specific SBATCH flags

source ${ROOT_DIR}/config.env
source ${PYTHON_ENV}/bin/activate 2>/dev/null || true
module load ${ADIOS2_MODULE} 2>/dev/null || true

export ADIOS2_CONFIG_FILE="${ROOT_DIR}/adios/adios2.xml"

# Rendezvous directory (must be on shared filesystem, visible to all nodes)
RENDEZVOUS_DIR="${BEEGFS_PATH}/adios_rendezvous_${SLURM_JOB_ID}"
mkdir -p "\${RENDEZVOUS_DIR}"

echo "=== Stage 1: Producers (ADIOS SST write) ==="
T_STAGE1_START=\$(date +%s)

# Launch N_TASKS producers simultaneously
# Each producer writes STAGE1_GB GB via SST
PRODUCER_PIDS=()
for i in \$(seq 0 $((N_TASKS-1))); do
    mpirun --bind-to none -np 1 python3 ${ROOT_DIR}/adios/producer_task.py \
        --output-name "\${RENDEZVOUS_DIR}/sim_out_\${i}" \
        --data-size-gb ${STAGE1_GB} \
        --transfer-size-mb 1 \
        > "${RESULTS_DIR}/producer_\${i}.log" 2>&1 &
    PRODUCER_PIDS+=(\$!)
done

echo "=== Stage 2: Consumers (ADIOS SST read) ==="
T_STAGE2_START=\$(date +%s)

# Launch N_TASKS consumers — must run SIMULTANEOUSLY with producers
CONSUMER_PIDS=()
for i in \$(seq 0 $((N_TASKS-1))); do
    mpirun --bind-to none -np 1 python3 ${ROOT_DIR}/adios/consumer_task.py \
        --input-name "\${RENDEZVOUS_DIR}/sim_out_\${i}" \
        --output-path "\${BEEGFS_PATH}/analysis_out_\${i}.bp" \
        > "${RESULTS_DIR}/consumer_\${i}.log" 2>&1 &
    CONSUMER_PIDS+=(\$!)
done

# Wait for all and collect exit codes
FAILED=0
for pid in "\${PRODUCER_PIDS[@]}"; do
    wait "\${pid}" || FAILED=\$((FAILED+1))
done
for pid in "\${CONSUMER_PIDS[@]}"; do
    wait "\${pid}" || FAILED=\$((FAILED+1))
done

T_END=\$(date +%s)
TOTAL_TIME=\$((T_END - T_STAGE1_START))

echo "RESULT: size=${SIZE}, backend=adios_sst, nodes=${NODES}" >> "${RESULTS_DIR}/result.txt"
echo "total_time_s=\${TOTAL_TIME}"  >> "${RESULTS_DIR}/result.txt"
echo "failed_tasks=\${FAILED}"      >> "${RESULTS_DIR}/result.txt"
echo "status=\$([ \${FAILED} -eq 0 ] && echo SUCCESS || echo FAILED)" >> "${RESULTS_DIR}/result.txt"

cat "${RESULTS_DIR}/result.txt"

# Cleanup rendezvous files
rm -rf "\${RENDEZVOUS_DIR}"
SLURM_EOF

echo "Submitting: sbatch ${JOB_SCRIPT}"
sbatch "${JOB_SCRIPT}"
echo "Monitor: tail -f ${RESULTS_DIR}/slurm_*.out"
