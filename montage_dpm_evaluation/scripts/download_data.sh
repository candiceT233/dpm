#!/bin/bash
# download_data.sh — Download 2MASS FITS images for Montage DPM evaluation
#
# Uses Montage's mArchiveDownload (Python) to fetch 2MASS J-band images
# from IRSA for a region around M17 (galactic plane, dense overlap).
#
# Usage:
#   bash scripts/download_data.sh --size small    # ~100 images, ~0.4 GB
#   bash scripts/download_data.sh --size medium   # ~400 images, ~1.8 GB
#   bash scripts/download_data.sh --size large    # ~1425 images, ~6.3 GB

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"

SIZE="large"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --size) SIZE="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

# Region sizes for each scale (degrees)
case "${SIZE}" in
    small)  REGION_DEG=2.0 ;;
    medium) REGION_DEG=4.0 ;;
    large)  REGION_DEG=6.0 ;;
    *) echo "Unknown size: ${SIZE}. Use small|medium|large"; exit 1 ;;
esac

SURVEY="2MASS J"
LOCATION="M17"   # RA~275.2, Dec~-16.17 (galactic plane, dense stellar field)

DATA_DIR="${ROOT_DIR}/data/${SIZE}/raw_images"
mkdir -p "${DATA_DIR}"

echo "=== Downloading ${SIZE} dataset ==="
echo "Survey: ${SURVEY}"
echo "Location: ${LOCATION}"
echo "Region: ${REGION_DEG} degrees"
echo "Output: ${DATA_DIR}"

# Use Montage's Python mArchiveDownload
MONTAGE_PY="${ROOT_DIR}/../../../hpc_workflows/repos/Montage/python/MontagePy"
if [[ ! -f "${MONTAGE_PY}/mArchiveDownload.py" ]]; then
    echo "ERROR: MontagePy not found at ${MONTAGE_PY}"
    echo "Set MONTAGE_PY to the path containing mArchiveDownload.py"
    exit 1
fi

echo ""
echo "Step 1: Querying IRSA archive for image list..."
python3 -c "
import sys
sys.path.insert(0, '${MONTAGE_PY}')
from mArchiveDownload import mArchiveDownload

print('Downloading images from IRSA... (this may take a while)')
result = mArchiveDownload('${SURVEY}', '${LOCATION}', ${REGION_DEG}, '${DATA_DIR}')
print(f'Result: {result}')
"

# Count downloaded images
N_FITS=$(ls "${DATA_DIR}"/*.fits 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh "${DATA_DIR}" | cut -f1)
echo ""
echo "=== Download complete ==="
echo "Images: ${N_FITS}"
echo "Total size: ${TOTAL_SIZE}"

# Generate region.hdr for this dataset
HDR_FILE="${ROOT_DIR}/data/${SIZE}/region.hdr"
echo ""
echo "Step 2: Generating region.hdr..."

# Pixel scale: 2MASS native ~1 arcsec/pixel = 0.000277 degrees
# Output size depends on region
# For 6 deg at 1 arcsec: 21600 pixels (too large for single mosaic)
# Use 2 arcsec/pixel for practical mosaic size
PIXEL_SCALE=0.000556  # ~2 arcsec/pixel
NAXIS=$(python3 -c "import math; print(int(math.ceil(${REGION_DEG} / ${PIXEL_SCALE})))")

cat > "${HDR_FILE}" << EOF
SIMPLE  = T
BITPIX  = -64
NAXIS   = 2
NAXIS1  = ${NAXIS}
NAXIS2  = ${NAXIS}
CTYPE1  = 'RA---TAN'
CTYPE2  = 'DEC--TAN'
CRVAL1  = 275.196
CRVAL2  = -16.172
CRPIX1  = $((NAXIS / 2))
CRPIX2  = $((NAXIS / 2))
CDELT1  = -${PIXEL_SCALE}
CDELT2  = ${PIXEL_SCALE}
CROTA2  = 0.0
EQUINOX = 2000.0
END
EOF

echo "Created: ${HDR_FILE}"
echo "  NAXIS: ${NAXIS} x ${NAXIS}"
echo "  Pixel scale: ${PIXEL_SCALE} deg (~2 arcsec)"
echo ""
echo "=== Ready for Montage pipeline ==="
echo "Next: bash scripts/run_montage.sh --size ${SIZE} --storage ssd --nodes 4"
