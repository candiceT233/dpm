#!/bin/bash
# run_storage.sh — Run the synthetic workflow using file-based storage (DPM config)
#
# This runs the same workflow as run_adios_sst.sh, but writes intermediate data
# to a specified storage tier (ssd, beegfs, tmpfs). DPM selects the best tier.
#
# Usage:
#   bash scripts/run_storage.sh --size small  --storage tmpfs  --nodes 4
#   bash scripts/run_storage.sh --size large  --storage ssd    --nodes 4
#   bash scripts/run_storage.sh --size large  --storage beegfs --nodes 4

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
RUN_ID="storage_${STORAGE}_${SIZE}_${NODES}n_${TIMESTAMP}"
RESULTS_DIR="${ROOT_DIR}/results/${RUN_ID}"
mkdir -p "${RESULTS_DIR}"

echo "=== Storage run: size=${SIZE}, storage=${STORAGE}, nodes=${NODES} ==="
echo "    Storage path: ${STORAGE_PATH}"
echo "    Results: ${RESULTS_DIR}"

# ── Extract metadata from workflow JSON ───────────────────────────────────────
WORKFLOW_JSON="${ROOT_DIR}/wfbench/workflow_${SIZE}.json"
if [[ ! -f "${WORKFLOW_JSON}" ]]; then
    echo "ERROR: ${WORKFLOW_JSON} not found."
    exit 1
fi

STAGE1_GB=$(python3 -c "
import json
wf = json.load(open('${WORKFLOW_JSON}'))
print(wf['dpmMeta']['stage1FileSizeBytes'] / 1024**3)
")
STAGE2_GB=$(python3 -c "
import json
wf = json.load(open('${WORKFLOW_JSON}'))
print(wf['dpmMeta']['stage2FileSizeBytes'] / 1024**3)
")
N_TASKS=$(python3 -c "
import json
wf = json.load(open('${WORKFLOW_JSON}'))
print(sum(1 for t in wf['workflow']['specification']['tasks'] if t['category']=='sim'))
")

# ── Write Slurm job script ────────────────────────────────────────────────────
JOB_SCRIPT="${RESULTS_DIR}/job_storage_${STORAGE}.sh"
cat > "${JOB_SCRIPT}" << SLURM_EOF
#!/bin/bash
#SBATCH --job-name=dpm_${STORAGE}_${SIZE}
#SBATCH --partition=${PARTITION}
#SBATCH --nodes=${NODES}
#SBATCH --ntasks-per-node=${CORES_PER_NODE}
#SBATCH --time=04:00:00
#SBATCH --output=${RESULTS_DIR}/slurm_%j.out
#SBATCH --error=${RESULTS_DIR}/slurm_%j.err
# TODO: add --account, --reservation, or other cluster-specific flags

source ${ROOT_DIR}/config.env
source ${PYTHON_ENV}/bin/activate 2>/dev/null || true

# Create per-job work directory on target storage
WORK_DIR="${STORAGE_PATH}/dpm_eval_\${SLURM_JOB_ID}"
mkdir -p "\${WORK_DIR}"

echo "=== Stage 1: Producers (writing to ${STORAGE}) ==="
T_STAGE1_START=\$(date +%s)

# Sequential write: N tasks write to STORAGE_PATH using IOR-like pattern
# Using dd as a simple stand-in; replace with actual simulation binary
PRODUCER_PIDS=()
for i in \$(seq 0 $((N_TASKS-1))); do
    OUT_FILE="\${WORK_DIR}/sim_out_\${i}.bin"
    SIZE_BYTES=\$(python3 -c "print(int(${STAGE1_GB} * 1024**3))")
    (
        dd if=/dev/zero of="\${OUT_FILE}" bs=1M count=\$((${STAGE1_GB%.*} * 1024)) \
            conv=fdatasync 2>&1
        echo "producer_\${i}: done writing \${OUT_FILE}"
    ) > "${RESULTS_DIR}/producer_\${i}.log" 2>&1 &
    PRODUCER_PIDS+=(\$!)
done

for pid in "\${PRODUCER_PIDS[@]}"; do wait "\${pid}"; done
T_STAGE1_END=\$(date +%s)
STAGE1_TIME=\$((T_STAGE1_END - T_STAGE1_START))
echo "Stage 1 time: \${STAGE1_TIME}s"

echo "=== Stage 2: Consumers (reading from ${STORAGE}, writing summary) ==="
T_STAGE2_START=\$(date +%s)

CONSUMER_PIDS=()
for i in \$(seq 0 $((N_TASKS-1))); do
    IN_FILE="\${WORK_DIR}/sim_out_\${i}.bin"
    OUT_FILE="\${WORK_DIR}/analysis_out_\${i}.bin"
    OUT_SIZE_BYTES=\$(python3 -c "print(int(${STAGE2_GB} * 1024**3))")
    (
        # Random read from IN_FILE, write reduced output
        # Using dd as a stand-in; replace with actual analysis binary
        dd if="\${IN_FILE}" of="\${OUT_FILE}" bs=4k \
            count=\$((${STAGE2_GB%.*} * 1024 * 256)) \
            iflag=nonblock conv=fdatasync 2>&1 || \
        dd if="\${IN_FILE}" of="\${OUT_FILE}" bs=4k conv=fdatasync 2>&1
        echo "consumer_\${i}: done"
    ) > "${RESULTS_DIR}/consumer_\${i}.log" 2>&1 &
    CONSUMER_PIDS+=(\$!)
done

for pid in "\${CONSUMER_PIDS[@]}"; do wait "\${pid}"; done
T_STAGE2_END=\$(date +%s)
STAGE2_TIME=\$((T_STAGE2_END - T_STAGE2_START))
echo "Stage 2 time: \${STAGE2_TIME}s"

echo "=== Stage 3: Aggregation ==="
T_STAGE3_START=\$(date +%s)
cat "\${WORK_DIR}"/analysis_out_*.bin > "\${WORK_DIR}/aggregate_out.bin" 2>&1
T_STAGE3_END=\$(date +%s)
STAGE3_TIME=\$((T_STAGE3_END - T_STAGE3_START))
echo "Stage 3 time: \${STAGE3_TIME}s"

T_TOTAL=\$((T_STAGE3_END - T_STAGE1_START))

echo "RESULT: size=${SIZE}, backend=${STORAGE}, nodes=${NODES}" > "${RESULTS_DIR}/result.txt"
echo "stage1_time_s=\${STAGE1_TIME}"  >> "${RESULTS_DIR}/result.txt"
echo "stage2_time_s=\${STAGE2_TIME}"  >> "${RESULTS_DIR}/result.txt"
echo "stage3_time_s=\${STAGE3_TIME}"  >> "${RESULTS_DIR}/result.txt"
echo "total_time_s=\${T_TOTAL}"       >> "${RESULTS_DIR}/result.txt"
echo "status=SUCCESS"                 >> "${RESULTS_DIR}/result.txt"
cat "${RESULTS_DIR}/result.txt"

# Cleanup work directory
rm -rf "\${WORK_DIR}"
SLURM_EOF

echo "Submitting: sbatch ${JOB_SCRIPT}"
sbatch "${JOB_SCRIPT}"
echo "Monitor: tail -f ${RESULTS_DIR}/slurm_*.out"
