#!/usr/bin/env bash
# run_chain.sh — Submit the medium/large evaluation Slurm dependency chain
#
# Run from the login node after config.env is filled in. This invokes
# scripts/submit_medium_large_evaluation.sh, which sbatch's each benchmark and
# chains them with --dependency=afterok (file trials 1–3, then ADIOS trials 2–3).
#
# Usage:
#   ./run_chain.sh [PREV_JOB_ID]
#   NODES=4 ./run_chain.sh
#
# See also: scripts/submit_medium_large_evaluation.sh (full job order).

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

usage() {
    cat <<'USAGE'
Usage: run_chain.sh [OPTIONS] [PREV_JOB_ID]

Submit one Slurm chain: file-based medium/large trials 1–3, then ADIOS SST
medium/large trials 2–3 (see scripts/submit_medium_large_evaluation.sh).

  PREV_JOB_ID   Optional. The first submitted job waits until this job
                finishes successfully (sbatch --dependency=afterok:ID).

Options:
  -h, --help    Show this help.

Environment:
  NODES         Node count for every job (default: 4).

Examples:
  ./run_chain.sh
  ./run_chain.sh 636219
  NODES=8 ./run_chain.sh

Monitor: squeue -u "$(whoami)" --sort=i
USAGE
}

if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

if [[ ! -f "${ROOT_DIR}/config.env" ]]; then
    echo "ERROR: ${ROOT_DIR}/config.env not found." >&2
    echo "Copy config.env.template to config.env and set cluster paths, account, partition." >&2
    exit 1
fi

echo "==> Submitting chain from ${ROOT_DIR}"
exec bash "${ROOT_DIR}/scripts/submit_medium_large_evaluation.sh" "$@"
