#!/bin/bash
# analyze_io_time.sh — Measure per-task I/O time vs compute time for Montage stages
#
# Uses strace -f -T to capture syscall wall time for each Montage binary.
# Runs each stage on real 2MASS small data and reports I/O % of wall time.
#
# Usage: bash analyze_io_time.sh > io_analysis.log

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"
source "${ROOT_DIR}/config.env"
export PATH="${MONTAGE_BIN}:${PATH}"

RAW="${ROOT_DIR}/data/small/raw_images"
HDR="${ROOT_DIR}/data/small/region.hdr"
TMP=$(mktemp -d /tmp/montage_io_analysis_XXXXXX)
trap "rm -rf ${TMP}" EXIT

mkdir -p "${TMP}/projected" "${TMP}/diffs" "${TMP}/corrected"

IO_SYSCALLS="read,write,openat,close,lseek,pread64,pwrite64,mmap,munmap,fstat,stat,lstat"

run_strace() {
    local LABEL="$1"
    shift
    local STRACE_OUT="${TMP}/strace_${LABEL}.txt"
    local TSTART=$(date +%s.%N)
    strace -f -T -ttt -o "${STRACE_OUT}" \
        -e trace="${IO_SYSCALLS}" \
        "$@" > /dev/null 2>&1
    local TEND=$(date +%s.%N)
    local WALL=$(echo "${TEND} - ${TSTART}" | bc)
    # Count unique PIDs (threads/forks)
    local N_THREADS=$(awk '{print $1}' "${STRACE_OUT}" | sort -u | wc -l)
    # Sum all syscall durations
    local IO_SUM=$(awk '{if (match($0, /<([0-9.]+)>/, arr)) total += arr[1]} END {printf "%.6f", total}' "${STRACE_OUT}")
    # Per-thread I/O time (approximates wall-clock I/O impact for parallel threads)
    local IO_PER_THREAD=$(echo "scale=6; ${IO_SUM} / ${N_THREADS}" | bc)
    # Percentage
    local PCT=$(echo "scale=2; (${IO_PER_THREAD} / ${WALL}) * 100" | bc)
    printf "%-20s wall=%8.3fs  threads=%2d  io_sum=%8.3fs  io_per_thread=%8.3fs  io_pct=%6.2f%%\n" \
        "${LABEL}" "${WALL}" "${N_THREADS}" "${IO_SUM}" "${IO_PER_THREAD}" "${PCT}"
    rm -f "${STRACE_OUT}"
}

echo "# Montage I/O Time Analysis"
echo "# Date: $(date)"
echo "# Dataset: 208 real 2MASS J-band FITS images"
echo "# Method: strace -f -T (follow forks, timed syscalls)"
echo "# Syscalls traced: ${IO_SYSCALLS}"
echo ""
echo "# Columns: task_name  wall_time  threads  io_sum  io_per_thread  io_percentage"
echo ""

echo "=== Stage 1: mImgtbl (raw image catalog) ==="
run_strace "mImgtbl_raw" mImgtbl "${RAW}" "${TMP}/images.tbl"

echo ""
echo "=== Stage 2: mProject (single image, reprojection) ==="
FIRST_RAW=$(ls "${RAW}"/*.fits | head -1)
run_strace "mProject_single" mProject "${FIRST_RAW}" "${TMP}/projected/test_proj.fits" "${HDR}"

# Do full mProjExec without strace to get projected images for next stages
mProjExec -p "${RAW}" "${TMP}/images.tbl" "${HDR}" "${TMP}/projected" "${TMP}/stats.tbl" 2>/dev/null

echo ""
echo "=== Stage 3: mImgtbl (projected image catalog) ==="
run_strace "mImgtbl_proj" mImgtbl "${TMP}/projected" "${TMP}/proj_images.tbl"

echo ""
echo "=== Stage 4: mOverlaps (identify overlapping pairs) ==="
run_strace "mOverlaps" mOverlaps "${TMP}/proj_images.tbl" "${TMP}/diffs.tbl"

echo ""
echo "=== Stage 5: mDiff (single pair difference) ==="
FIRST_PAIR=$(awk '!/^[\\|]/' "${TMP}/diffs.tbl" | head -1)
PLUS=$(echo "${FIRST_PAIR}" | awk '{print $3}')
MINUS=$(echo "${FIRST_PAIR}" | awk '{print $4}')
DIFFNAME=$(echo "${FIRST_PAIR}" | awk '{print $5}')
run_strace "mDiff_single" mDiff "${PLUS}" "${MINUS}" "${TMP}/diffs/${DIFFNAME}" "${HDR}"

# Full mDiffExec and mFitExec for later stages
mDiffExec -p "${TMP}/projected" "${TMP}/diffs.tbl" "${HDR}" "${TMP}/diffs" 2>/dev/null

echo ""
echo "=== Stage 6: mFitExec (plane fitting, serial over all diffs) ==="
run_strace "mFitExec" mFitExec "${TMP}/diffs.tbl" "${TMP}/fits.tbl" "${TMP}/diffs"

echo ""
echo "=== Stage 7: mBgModel (background modeling, serial) ==="
run_strace "mBgModel" mBgModel "${TMP}/proj_images.tbl" "${TMP}/fits.tbl" "${TMP}/corrections.tbl"

echo ""
echo "=== Stage 8: mBackground (single image correction) ==="
FIRST_PROJ=$(ls "${TMP}/projected"/*.fits | head -1)
run_strace "mBackground_single" mBackground "${FIRST_PROJ}" "${TMP}/corrected/test_corr.fits" 0.0 0.0 0.0

# Full mBgExec for final stages
mBgExec -p "${TMP}/projected" "${TMP}/proj_images.tbl" "${TMP}/corrections.tbl" "${TMP}/corrected" 2>/dev/null

echo ""
echo "=== Stage 9: mImgtbl (corrected image catalog) ==="
run_strace "mImgtbl_corr" mImgtbl "${TMP}/corrected" "${TMP}/corr_images.tbl"

echo ""
echo "=== Stage 10: mAdd (final mosaic coaddition) ==="
run_strace "mAdd" mAdd -p "${TMP}/corrected" "${TMP}/corr_images.tbl" "${HDR}" "${TMP}/mosaic.fits"

echo ""
echo "# Analysis complete"
