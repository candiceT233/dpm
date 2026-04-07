#!/bin/bash
# collect_results.sh — Gather all result.txt files into a single CSV
#
# Usage:
#   bash scripts/collect_results.sh --output results/all_results.csv

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"
RESULTS_BASE="${ROOT_DIR}/results"
OUTPUT="${RESULTS_BASE}/all_results.csv"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --output) OUTPUT="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

echo "Collecting results from ${RESULTS_BASE}/"
echo "size,backend,nodes,stage1_time_s,stage2_time_s,stage3_time_s,total_time_s,status" > "${OUTPUT}"

for result_file in "${RESULTS_BASE}"/*/result.txt; do
    if [[ ! -f "${result_file}" ]]; then continue; fi

    parse() { grep "^${1}=" "${result_file}" | cut -d= -f2 || echo "NA"; }

    # Extract run metadata from directory name
    dir_name=$(basename "$(dirname "${result_file}")")
    # Format: {backend}_{size}_{nodes}n_{timestamp}
    BACKEND=$(echo "${dir_name}" | cut -d_ -f1-2 | sed 's/_[0-9]*n_.*//')
    SIZE=$(echo "${dir_name}" | grep -oP '(small|medium|large)')
    NODES_VAL=$(echo "${dir_name}" | grep -oP '[0-9]+(?=n_)')

    echo "${SIZE},${BACKEND},${NODES_VAL},$(parse stage1_time_s),$(parse stage2_time_s),$(parse stage3_time_s),$(parse total_time_s),$(parse status)"
done >> "${OUTPUT}"

echo "Results written to: ${OUTPUT}"
echo ""
cat "${OUTPUT}"
