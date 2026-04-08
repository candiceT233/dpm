#!/bin/bash
# collect_results.sh — Gather all Montage result.txt files into a single CSV
#
# Usage:
#   bash scripts/collect_results.sh
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

# CSV header — per-stage timing + data sizes
echo "size,backend,nodes,mImgtbl_s,mProjExec_s,mOverlaps_s,mDiffExec_s,mFitExec_s,mBgModel_s,mBgExec_s,mAdd_s,total_time_s,n_images,n_pairs,total_intermediate_bytes,status" > "${OUTPUT}"

for result_file in "${RESULTS_BASE}"/*/result.txt; do
    if [[ ! -f "${result_file}" ]]; then continue; fi

    parse() { grep "^${1}=" "${result_file}" | cut -d= -f2 || echo "NA"; }

    # Extract run metadata from directory name: {backend}_{size}_{nodes}n_{timestamp}
    dir_name=$(basename "$(dirname "${result_file}")")
    BACKEND=$(echo "${dir_name}" | cut -d_ -f1)
    SIZE=$(echo "${dir_name}" | grep -oP '(small|medium|large)')
    NODES_VAL=$(echo "${dir_name}" | grep -oP '[0-9]+(?=n_)')

    echo "${SIZE},${BACKEND},${NODES_VAL},$(parse mImgtbl_time_s),$(parse mProjExec_time_s),$(parse mOverlaps_time_s),$(parse mDiffExec_time_s),$(parse mFitExec_time_s),$(parse mBgModel_time_s),$(parse mBgExec_time_s),$(parse mAdd_time_s),$(parse total_time_s),$(parse n_images),$(parse n_pairs),$(parse total_intermediate_bytes),$(parse status)"
done >> "${OUTPUT}"

echo "Results written to: ${OUTPUT}"
echo ""
cat "${OUTPUT}" | column -t -s,
