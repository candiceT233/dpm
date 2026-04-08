#!/bin/bash
# setup_env.sh — Environment setup for Montage DPM evaluation
# Run this once on the login node before submitting jobs.
#
# Usage: bash scripts/setup_env.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"

# ── Load config ──────────────────────────────────────────────────────────────
CONFIG_FILE="${ROOT_DIR}/config.env"
if [[ ! -f "${CONFIG_FILE}" ]]; then
    echo "ERROR: config.env not found at ${CONFIG_FILE}"
    echo "Copy config.env.template to config.env and fill in cluster settings"
    exit 1
fi
source "${CONFIG_FILE}"

# ── Compile Montage (if not already built) ───────────────────────────────────
echo "==> Checking Montage binaries"
if [[ -n "${MONTAGE_BIN}" ]] && [[ -f "${MONTAGE_BIN}/mImgtbl" ]]; then
    echo "  Montage binaries found at ${MONTAGE_BIN}"
else
    echo "  ERROR: Montage binaries not found at ${MONTAGE_BIN}"
    echo "  Compile Montage first:"
    echo "    cd /path/to/Montage && make"
    echo "  Then set MONTAGE_BIN in config.env"
    exit 1
fi

# ── Verify Montage tools ────────────────────────────────────────────────────
echo "==> Verifying Montage tools"
for tool in mImgtbl mProjExec mOverlaps mDiffExec mFitExec mBgModel mBgExec mAdd; do
    if [[ -f "${MONTAGE_BIN}/${tool}" ]]; then
        echo "  ${tool}: OK"
    else
        echo "  ${tool}: MISSING"
    fi
done

# ── Python environment (for data download and analysis) ─────────────────────
echo "==> Setting up Python environment"
if [[ -n "${PYTHON_ENV}" ]] && [[ -d "${PYTHON_ENV}" ]]; then
    echo "  Activating existing env: ${PYTHON_ENV}"
    source "${PYTHON_ENV}/bin/activate"
else
    echo "  Creating new venv"
    python3 -m venv "${ROOT_DIR}/.venv"
    source "${ROOT_DIR}/.venv/bin/activate"
fi

pip install --quiet --upgrade pip
pip install --quiet numpy pandas matplotlib

echo "==> Verifying Python packages"
python3 -c "import numpy;  print(f'  numpy:  {numpy.__version__}')"
python3 -c "import pandas; print(f'  pandas: {pandas.__version__}')"

# ── Verify storage paths ────────────────────────────────────────────────────
echo "==> Verifying storage paths"
for PATH_VAR in LOCAL_SSD_PATH BEEGFS_PATH TMPFS_PATH; do
    VAL="${!PATH_VAR}"
    if [[ -d "${VAL}" ]]; then
        echo "  ${PATH_VAR}=${VAL} : OK ($(df -h "${VAL}" | tail -1 | awk '{print $4}') free)"
    else
        echo "  WARNING: ${PATH_VAR}=${VAL} does not exist"
    fi
done

# ── Verify Darshan (optional) ───────────────────────────────────────────────
if [[ -n "${DARSHAN_LIB}" ]] && [[ -f "${DARSHAN_LIB}" ]]; then
    echo "==> Darshan I/O tracing: ${DARSHAN_LIB}"
else
    echo "==> Darshan: not configured (optional — set DARSHAN_LIB in config.env)"
fi

echo ""
echo "==> Setup complete."
echo "Next steps:"
echo "  1. Download data:  bash scripts/download_data.sh --size large"
echo "  2. Run experiment: bash scripts/run_montage.sh --size large --storage ssd --nodes 4"
