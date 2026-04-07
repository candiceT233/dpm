#!/bin/bash
# setup_env.sh — Environment setup for WfBench ADIOS vs DPM experiment
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
    echo "Copy and fill in the template from PLAN.md Step 0"
    exit 1
fi
source "${CONFIG_FILE}"

# ── Load cluster modules ──────────────────────────────────────────────────────
echo "==> Loading cluster modules"
module purge 2>/dev/null || true

# TODO: Adjust module names for your cluster
# Example for PNNL clusters:
# module load python/3.11
# module load ${ADIOS2_MODULE}
# module load openmpi/4.1.5

echo "  [TODO] Uncomment and edit module load commands for ${CLUSTER_NAME}"

# ── Python environment ────────────────────────────────────────────────────────
echo "==> Setting up Python environment"

if [[ -n "${PYTHON_ENV}" ]] && [[ -d "${PYTHON_ENV}" ]]; then
    echo "  Activating existing env: ${PYTHON_ENV}"
    source "${PYTHON_ENV}/bin/activate"
else
    echo "  Creating new conda/venv environment"
    # Option A: conda
    # conda create -n dpm_adios_eval python=3.11 -y
    # conda activate dpm_adios_eval

    # Option B: venv
    python3 -m venv "${ROOT_DIR}/.venv"
    source "${ROOT_DIR}/.venv/bin/activate"
fi

# ── Install Python dependencies ───────────────────────────────────────────────
echo "==> Installing Python packages"
pip install --quiet --upgrade pip

# WfCommons (WfBench)
pip install --quiet "wfcommons>=1.4"

# ADIOS2 Python bindings
# NOTE: If ADIOS2 is installed via module, skip pip install and use module's Python bindings
# If building from source or using pip:
pip install --quiet adios2 || echo "  WARNING: adios2 pip install failed — try system module"

# Other dependencies
pip install --quiet mpi4py numpy pandas matplotlib

echo "==> Verifying installations"
python -c "import wfcommons; print(f'  wfcommons: {wfcommons.__version__}')"
python -c "import adios2;    print(f'  adios2:    {adios2.__version__}')" || echo "  adios2: not importable via pip — check cluster module"
python -c "import mpi4py;    print(f'  mpi4py:    {mpi4py.__version__}')"
python -c "import numpy;     print(f'  numpy:     {numpy.__version__}')"

echo "==> Verifying storage paths"
for PATH_VAR in LOCAL_SSD_PATH BEEGFS_PATH TMPFS_PATH; do
    VAL="${!PATH_VAR}"
    if [[ -d "${VAL}" ]]; then
        echo "  ${PATH_VAR}=${VAL} : OK ($(df -h "${VAL}" | tail -1 | awk '{print $4}') free)"
    else
        echo "  WARNING: ${PATH_VAR}=${VAL} does not exist"
    fi
done

echo ""
echo "==> Setup complete. Run 'source config.env' in your job scripts."
