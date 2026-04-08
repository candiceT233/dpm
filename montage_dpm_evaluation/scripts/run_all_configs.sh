#!/bin/bash
# run_all_configs.sh — Submit all 9 DPM evaluation configurations (3 runs each)
#
# Usage:
#   bash scripts/run_all_configs.sh --size large
#   bash scripts/run_all_configs.sh --size large --dry-run   # Print commands only

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SIZE="large"
DRY_RUN=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --size)    SIZE="$2";  shift 2 ;;
        --dry-run) DRY_RUN=1;  shift   ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

echo "=== Montage DPM Evaluation: All Configurations ==="
echo "Data size: ${SIZE}"
echo ""

STORAGES=(ssd beegfs tmpfs)
NODE_COUNTS=(4 8 16)
RUNS_PER_CONFIG=3

TOTAL=0
for storage in "${STORAGES[@]}"; do
    for nodes in "${NODE_COUNTS[@]}"; do
        for run in $(seq 1 ${RUNS_PER_CONFIG}); do
            TOTAL=$((TOTAL + 1))
            CMD="bash ${SCRIPT_DIR}/run_montage.sh --size ${SIZE} --storage ${storage} --nodes ${nodes}"
            echo "[${TOTAL}] ${CMD}  (run ${run}/${RUNS_PER_CONFIG})"
            if [[ ${DRY_RUN} -eq 0 ]]; then
                ${CMD}
                sleep 2  # brief pause between submissions
            fi
        done
    done
done

echo ""
echo "Total jobs submitted: ${TOTAL}"
echo "Monitor: squeue -u \$(whoami)"
echo "Collect results: bash scripts/collect_results.sh"
