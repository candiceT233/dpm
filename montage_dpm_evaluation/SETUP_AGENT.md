# SETUP_AGENT.md — Onboarding Guide for Montage DPM Evaluation

This file is written for an AI terminal agent or human setting up this evaluation
**from scratch on a fresh HPC cluster**. It is intended to be self-contained:
following the steps in order will produce a working Montage installation, the
input dataset, and the full evaluation results — with no path or tool assumed
to exist outside what this guide installs or detects.

It covers: discovering the cluster environment, compiling Montage from source,
downloading ~6.3 GB of FITS data from IRSA, and running the full 10-stage
pipeline across storage-parallelism configurations.

**Key constraint**: The input data (~1,425 FITS images, ~6.3 GB) cannot be
transferred from another machine. It must be downloaded directly on the cluster
from IRSA (NASA/IPAC Infrared Science Archive) using Montage's built-in Python
downloader or curl/wget.

## Conventions used below

Throughout this guide, paths are written with shell variables instead of
hardcoded absolute paths so the instructions work on any cluster:

| Variable      | Meaning                                                        |
|---------------|----------------------------------------------------------------|
| `${ROOT_DIR}` | This evaluation folder (the directory containing `README.md`)  |
| `${MONTAGE_SRC}` | Where you cloned the Montage source tree                    |
| `${INSTALL_PREFIX}` | A directory you control for software installs (e.g. `${HOME}/install`) |

Pick concrete values for these once at the start of your session, e.g.:

```bash
export ROOT_DIR="$(pwd)"                       # if you are in this folder
export INSTALL_PREFIX="${HOME}/install"
export MONTAGE_SRC="${INSTALL_PREFIX}/Montage"
mkdir -p "${INSTALL_PREFIX}"
```

## Prerequisites (verify these before starting)

The cluster must provide:

- **Compilers and build tools**: `gcc`, `make` (Montage compiles from C source).
- **Python ≥ 3.8**: for IRSA download and analysis. A user-writable virtualenv
  or conda env is sufficient — no system-Python modifications needed.
- **Slurm**: for batch submission (`sbatch`, `srun`, `squeue`, `scontrol`).
- **Internet access from at least one node** (login node is fine) to reach
  `irsa.ipac.caltech.edu` for the 2MASS dataset.
- **At least three storage tiers reachable from compute nodes**: a node-local
  SSD, a shared parallel filesystem (BeeGFS / Lustre / GPFS / NFS), and tmpfs
  (`/dev/shm`). The probe in Step 0 will detect them.
- **Disk budget**: ~7 GB for raw FITS, ~30 GB peak per run for intermediate
  data (large config), ~5–10 GB for output mosaics across all runs.

No root/sudo access is required. Everything installs into `${INSTALL_PREFIX}`.

---

## Step 0: Discover Cluster Environment

Run these commands to collect the information needed for `config.env`.

### Identify yourself and your allocations

```bash
whoami
groups
sacctmgr show user $(whoami) withassoc format=user,account,partition -p 2>/dev/null || \
  echo "Try: squeue --me or check with cluster admin"
```

### Find partition and node specs

```bash
# List available partitions
sinfo -o "%P %N %m %c %G" | head -20

# Check node details
scontrol show node $(sinfo -t idle -o "%n" --noheader | head -1) | \
  grep -E "NodeName|CPUTot|RealMemory|Gres"
```

### Probe a compute node for storage paths

Submit a short job to discover storage mounts on a compute node:

```bash
ACCOUNT="YOUR_ACCOUNT"    # from sacctmgr output above
PARTITION="YOUR_PARTITION" # from sinfo output above

sbatch --partition=${PARTITION} --account=${ACCOUNT} \
       --nodes=1 --ntasks=1 --time=00:05:00 \
       --output=/tmp/probe_$$.out --error=/tmp/probe_$$.err \
       --wrap="
echo '=== Node: '\$(hostname)
echo '=== CPUs:' \$(nproc)
echo '=== RAM:' && free -h
echo '=== Storage mounts:'
df -hT | grep -v tmpfs | grep -v overlay
echo '=== Local storage paths:'
for p in /local /local/scratch /nvme /scratch /tmp/scratch; do
    [ -d \"\$p\" ] && echo \"  EXISTS: \$p (\$(df -h \$p | tail -1 | awk '{print \$4}') free)\" || true
done
echo '=== TMPFS (/dev/shm):'
df -h /dev/shm
echo '=== Internet connectivity (needed for IRSA download):'
curl -s --connect-timeout 5 -o /dev/null -w '%{http_code}' http://irsa.ipac.caltech.edu/ || echo 'NO_INTERNET'
echo '=== Python:'
python3 --version 2>/dev/null || echo 'python3 not found'
which python3 2>/dev/null
echo '=== GCC (for compiling Montage):'
gcc --version 2>/dev/null | head -1 || echo 'gcc not found'
echo '=== PROBE COMPLETE ==='
"
```

Wait for job to finish, then check output:

```bash
squeue --me
cat /tmp/probe_$$.out
cat /tmp/probe_$$.err
```

**Critical check**: The probe must show `200` for the IRSA connectivity test.
If compute nodes have no internet access, you must download data on the login
node instead (see Step 3 alternative).

Record from the probe:
- **CPUs** (`nproc`) → `CORES_PER_NODE`
- **RAM** (`free -h` Mem total) → `MEM_PER_NODE_GB`
- **Local SSD** (whichever of `/local/scratch`, `/nvme` exists) → `LOCAL_SSD_PATH`
- **Shared FS** (BeeGFS/Lustre/GPFS line from `df -hT`) → `BEEGFS_PATH`
- **TMPFS** (`df -h /dev/shm`) → capacity determines if tmpfs configs are feasible

---

## Step 1: Fill in config.env

```bash
cd "${ROOT_DIR}"
cp config.env.template config.env
```

Edit `config.env` — replace every `TODO` with values from the probe (Step 0)
and from the install steps that follow. Use whatever your cluster's actual
names are; the example below shows the **shape** of the values, not literal
paths to copy.

```bash
CLUSTER_NAME="<your cluster>"          # e.g. deception, tahoma, perlmutter
PARTITION="<slurm partition>"          # from sinfo
ACCOUNT="<slurm account>"              # from sacctmgr

CORES_PER_NODE=<int>                   # from probe (nproc)
MEM_PER_NODE_GB=<int>                  # from probe (free -h)

LOCAL_SSD_PATH="<node-local SSD mount>"  # from probe, e.g. /local/scratch, /nvme
BEEGFS_PATH="<shared parallel FS path>"  # from probe, e.g. /rcfs/projects/<acct>
TMPFS_PATH="/dev/shm"

MONTAGE_BIN="${MONTAGE_SRC}/bin"             # filled in after Step 2
MONTAGE_PY="${MONTAGE_SRC}/python/MontagePy" # filled in after Step 2 — used by download_data.sh
MONTAGE_DATA="${ROOT_DIR}/data"
PYTHON_ENV="${ROOT_DIR}/.venv"               # or path to a conda env
DARSHAN_LIB=""                               # Optional — path to libdarshan.so
DARSHAN_LOG_DIR=""                           # Optional — log root; defaults to ${ROOT_DIR}/results/darshan-logs
DPM_PROFILE_DIR=""                           # Optional
```

---

## Step 2: Compile Montage and Set Up Python

This step builds Montage from source into `${MONTAGE_SRC}` and creates a
Python virtualenv inside `${ROOT_DIR}`. Both produce the values you put into
`config.env` (`MONTAGE_BIN`, `MONTAGE_PY`, `PYTHON_ENV`).

### Compile Montage from source

Montage is a self-contained C toolkit with no external dependencies beyond a
working C compiler:

```bash
# Pick an install location you control
export INSTALL_PREFIX="${INSTALL_PREFIX:-${HOME}/install}"
mkdir -p "${INSTALL_PREFIX}"
cd "${INSTALL_PREFIX}"

# Clone the upstream repo
git clone https://github.com/Caltech-IPAC/Montage.git
export MONTAGE_SRC="${INSTALL_PREFIX}/Montage"
cd "${MONTAGE_SRC}"

# Apply patch if needed (JPEG library fix for some systems).
# Only needed if compilation fails on jconfig.h:
# sed -i 's/#define DONT_USE_B_MODE 1/\/* #undef DONT_USE_B_MODE *\//' \
#     lib/src/jpeg-8b/jconfig.h

make

# Verify binaries exist
ls "${MONTAGE_SRC}/bin/mImgtbl" \
   "${MONTAGE_SRC}/bin/mProjExec" \
   "${MONTAGE_SRC}/bin/mOverlaps" \
   "${MONTAGE_SRC}/bin/mDiffExec" \
   "${MONTAGE_SRC}/bin/mFitExec" \
   "${MONTAGE_SRC}/bin/mBgModel" \
   "${MONTAGE_SRC}/bin/mBgExec" \
   "${MONTAGE_SRC}/bin/mAdd"

# Verify the Python helpers ship with the source tree
ls "${MONTAGE_SRC}/python/MontagePy/mArchiveDownload.py"

# Record the paths for config.env
echo "MONTAGE_BIN=${MONTAGE_SRC}/bin"
echo "MONTAGE_PY=${MONTAGE_SRC}/python/MontagePy"
```

Update `MONTAGE_BIN` and `MONTAGE_PY` in `config.env` to those paths.
`MONTAGE_PY` is required by `scripts/download_data.sh` (Step 3) — without it,
the download will fail with a clear error.

### Set up Python environment

Python is needed for data download and analysis (not for the Montage pipeline itself):

```bash
cd "${ROOT_DIR}"
python3 -m venv "${ROOT_DIR}/.venv"
source "${ROOT_DIR}/.venv/bin/activate"

pip install --upgrade pip
pip install numpy pandas matplotlib

# Update PYTHON_ENV in config.env
echo "PYTHON_ENV=${ROOT_DIR}/.venv"
```

If your cluster prefers conda, substitute a conda env path for `${ROOT_DIR}/.venv`
and set `PYTHON_ENV` accordingly.

### Verify setup

```bash
cd "${ROOT_DIR}"
bash scripts/setup_env.sh
```

This checks: Montage binaries, Python packages, storage paths. It is safe to
re-run — it only verifies and (if needed) creates `${ROOT_DIR}/.venv`.

---

## Step 3: Download Input Data from IRSA

**This is the critical step.** The data must be downloaded directly on the
cluster. There are three methods depending on your cluster's setup.

### Data specification

| Parameter | Value |
|-----------|-------|
| Survey | 2MASS J-band (1.25 μm near-infrared) |
| Sky region | M17 (Omega Nebula), RA≈275.2°, Dec≈-16.17° |
| Region size | 6 degrees (for large dataset) |
| Expected images | ~1,425 FITS files |
| Expected size | ~6.3 GB (decompressed) |
| Source | IRSA (NASA/IPAC Infrared Science Archive) |

### Method A: Use the download script (recommended)

`scripts/download_data.sh` reads `MONTAGE_PY` from `config.env`, calls
`mArchiveDownload`, and also generates the `region.hdr` mosaic header. This
is the simplest path and is what the rest of the pipeline expects.

```bash
cd "${ROOT_DIR}"
bash scripts/download_data.sh --size large
```

**Expected output**: ~1,425 FITS files in `${ROOT_DIR}/data/large/raw_images`,
~6.3 GB total, plus `${ROOT_DIR}/data/large/region.hdr`.

If `MONTAGE_PY` is unset or wrong, the script exits with a clear error pointing
back to `config.env`.

### Method B: Call mArchiveDownload directly

Useful if you want to debug download issues without the wrapper script:

```bash
cd "${ROOT_DIR}"
source config.env                     # picks up MONTAGE_PY
mkdir -p "${ROOT_DIR}/data/large/raw_images"

python3 -c "
import sys
sys.path.insert(0, '${MONTAGE_PY}')
from mArchiveDownload import mArchiveDownload

print('Downloading 2MASS J-band images from IRSA...')
print('Survey: 2MASS J, Location: M17, Size: 6.0 degrees')
print('This will download ~1,425 FITS files (~6.3 GB). This may take 30-60 minutes.')
print()

result = mArchiveDownload('2MASS J', 'M17', 6.0, '${ROOT_DIR}/data/large/raw_images')
print(f'Result: {result}')
"

# Verify download
echo "Downloaded $(ls ${ROOT_DIR}/data/large/raw_images/*.fits | wc -l) FITS files"
echo "Total size:  $(du -sh ${ROOT_DIR}/data/large/raw_images | cut -f1)"
```

Note: Method B does **not** generate `region.hdr` — if you go this route, run
the header-generation block in "Generate region.hdr" below before continuing.

### Method C: Manual download with curl (if MontagePy fails)

If the Python downloader fails (SSL issues, timeouts), you can query the
archive API directly and download with curl/wget:

```bash
mkdir -p "${ROOT_DIR}/data/large/raw_images"
cd "${ROOT_DIR}/data/large"

# Step 1: Query IRSA for the image list (JSON)
curl -s "http://montage.ipac.caltech.edu/cgi-bin/ArchiveList/nph-archivelist?survey=2MASS+J&location=M17&size=6.0&units=deg&mode=JSON" \
  -o archive_list.json

# Step 2: Count images
python3 -c "import json; data=json.load(open('archive_list.json')); print(f'Found {len(data)} images')"

# Step 3: Download all images (parallel with xargs for speed)
python3 -c "
import json
data = json.load(open('archive_list.json'))
with open('download_urls.txt', 'w') as f:
    for entry in data:
        url = entry['url']
        fname = entry['file']
        # Remove .bz2 extension for output filename
        if fname.endswith('.bz2'):
            fname = fname[:-4]
        f.write(f'{url}\t{fname}\n')
print(f'Wrote {len(data)} URLs to download_urls.txt')
"

# Download files (4 parallel downloads)
# Note: 2MASS files are bzip2-compressed; decompress on the fly
cat download_urls.txt | while IFS=$'\t' read -r url fname; do
    echo "Downloading: ${fname}"
    curl -s "${url}" | bzcat > "raw_images/${fname}" 2>/dev/null || \
    curl -s "${url}" -o "raw_images/${fname}"
done

# Or faster with GNU parallel (if available):
# cat download_urls.txt | parallel -j 8 --colsep '\t' \
#   'curl -s {1} | bzcat > raw_images/{2} 2>/dev/null || curl -s {1} -o raw_images/{2}'

echo "Downloaded $(ls raw_images/*.fits | wc -l) files"
echo "Total size: $(du -sh raw_images | cut -f1)"
```

### Method D: Generate synthetic FITS files (if IRSA is unreachable)

If the cluster has NO internet access at all, you can generate synthetic
FITS files with the correct headers for Montage to process. This tests
the I/O pipeline without real astronomical data:

```bash
mkdir -p "${ROOT_DIR}/data/large/raw_images"
cd "${ROOT_DIR}"

python3 << 'PYEOF'
import numpy as np
import struct
import os

out_dir = "data/large/raw_images"
n_images = 1425  # Match expected count
image_size = 512  # pixels per side (512x512 float32 = ~1MB per image)

# Generate images in a grid covering 6 degrees around M17
ra_center, dec_center = 275.196, -16.172
region_deg = 6.0
pixel_scale = 0.000277  # ~1 arcsec/pixel (2MASS native)
fov_per_image = image_size * pixel_scale  # ~0.14 deg per image

# Grid layout
n_side = int(np.ceil(np.sqrt(n_images)))
ra_offsets = np.linspace(-region_deg/2, region_deg/2, n_side)
dec_offsets = np.linspace(-region_deg/2, region_deg/2, n_side)

count = 0
for i, ra_off in enumerate(ra_offsets):
    for j, dec_off in enumerate(dec_offsets):
        if count >= n_images:
            break
        ra = ra_center + ra_off
        dec = dec_center + dec_off

        # Create minimal FITS file with correct WCS headers
        # FITS header: 2880-byte blocks, each card is 80 chars
        cards = [
            f"SIMPLE  =                    T / Standard FITS",
            f"BITPIX  =                  -32 / 32-bit float",
            f"NAXIS   =                    2 / 2D image",
            f"NAXIS1  =                  {image_size} / pixels",
            f"NAXIS2  =                  {image_size} / pixels",
            f"CTYPE1  = 'RA---TAN'           / Gnomonic projection",
            f"CTYPE2  = 'DEC--TAN'           / Gnomonic projection",
            f"CRVAL1  =    {ra:16.10f} / RA center [deg]",
            f"CRVAL2  =    {dec:16.10f} / Dec center [deg]",
            f"CRPIX1  =    {image_size/2 + 0.5:16.10f} / Ref pixel X",
            f"CRPIX2  =    {image_size/2 + 0.5:16.10f} / Ref pixel Y",
            f"CDELT1  =  {-pixel_scale:18.12f} / deg/pixel",
            f"CDELT2  =  {pixel_scale:19.12f} / deg/pixel",
            f"CROTA2  =    0.0000000000 / Rotation [deg]",
            f"EQUINOX =               2000.0 / J2000",
            f"END",
        ]

        # Pad each card to 80 chars, pad header to multiple of 2880
        header_str = ""
        for card in cards:
            header_str += card.ljust(80)
        # Pad to 2880 boundary
        remainder = len(header_str) % 2880
        if remainder > 0:
            header_str += " " * (2880 - remainder)

        # Image data: random noise (float32, big-endian as FITS requires)
        data = np.random.normal(100, 10, (image_size, image_size)).astype('>f4')

        fname = f"{out_dir}/synth_{count:05d}.fits"
        with open(fname, 'wb') as f:
            f.write(header_str.encode('ascii'))
            f.write(data.tobytes())

        count += 1
        if count % 100 == 0:
            print(f"  Generated {count}/{n_images} images...")
    if count >= n_images:
        break

print(f"Generated {count} synthetic FITS files in {out_dir}")
print(f"Total size: {count * image_size * image_size * 4 / 1024**3:.2f} GB")
PYEOF
```

**Note on synthetic data**: Synthetic images produce valid Montage runs but
the pixel values are random noise. The I/O patterns, file sizes, and pipeline
behavior are identical to real data — only the scientific content differs.
This is sufficient for DPM evaluation since DPM measures I/O performance,
not astronomical accuracy.

### Generate region.hdr (required for all methods)

After downloading/generating images, create the mosaic target header.
Method A already does this for you — only run this block if you used Method B,
C, or D.

```bash
# For the large (6-degree) dataset
cat > "${ROOT_DIR}/data/large/region.hdr" << 'EOF'
SIMPLE  = T
BITPIX  = -64
NAXIS   = 2
NAXIS1  = 10792
NAXIS2  = 10792
CTYPE1  = 'RA---TAN'
CTYPE2  = 'DEC--TAN'
CRVAL1  = 275.196
CRVAL2  = -16.172
CRPIX1  = 5396
CRPIX2  = 5396
CDELT1  = -0.000556
CDELT2  = 0.000556
CROTA2  = 0.0
EQUINOX = 2000.0
END
EOF

echo "Created ${ROOT_DIR}/data/large/region.hdr"
```

### Verify data is ready

```bash
source "${ROOT_DIR}/config.env"   # provides MONTAGE_BIN

N_FITS=$(ls "${ROOT_DIR}/data/large/raw_images"/*.fits 2>/dev/null | wc -l)
DATA_SIZE=$(du -sh "${ROOT_DIR}/data/large/raw_images" 2>/dev/null | cut -f1)
echo "FITS files: ${N_FITS}"
echo "Total size: ${DATA_SIZE}"
echo "region.hdr: $([ -f ${ROOT_DIR}/data/large/region.hdr ] && echo 'OK' || echo 'MISSING')"

# Quick Montage validation — does mImgtbl parse the images?
export PATH="${MONTAGE_BIN}:${PATH}"
mImgtbl "${ROOT_DIR}/data/large/raw_images" /tmp/test_images.tbl
echo "mImgtbl found $(grep -c '|' /tmp/test_images.tbl) valid images"
rm -f /tmp/test_images.tbl
```

**Expected**: ~1,425 FITS files, ~6.3 GB (real) or ~1.4 GB (synthetic 512×512),
region.hdr present, mImgtbl reports ~1,425 valid images.

---

## Step 4: Test with Small Dataset First

Before running the full 27-job experiment, verify the pipeline works end-to-end
with a small dataset:

```bash
# Download small data (2-degree, ~100 images, ~0.4 GB)
bash scripts/download_data.sh --size small

# Run single test on login node (if allowed) or via sbatch
bash scripts/run_montage.sh --size small --storage ssd --nodes 4

# Check result
cat results/ssd_small_4n_*/result.txt
```

If the test succeeds (status=SUCCESS, mosaic.fits created), proceed to Step 5.

---

## Step 5: Run Full Experiment

### Submit all 27 jobs

```bash
# Dry run first — prints commands without submitting
bash scripts/run_all_configs.sh --size large --dry-run

# Submit for real
bash scripts/run_all_configs.sh --size large
```

This submits: 3 storage (ssd, beegfs, tmpfs) × 3 nodes (4, 8, 16) × 3 runs = 27 jobs.

### Monitor progress

```bash
squeue --me
# Check individual results as they finish:
ls results/*/result.txt | wc -l    # how many completed
cat results/*/result.txt | grep status
```

### Collect results

```bash
bash scripts/collect_results.sh
python analysis/compare_results.py --results results/all_results.csv --output results/
```

---

## Step 6: Troubleshooting

### mArchiveDownload hangs or times out

The IRSA server may rate-limit or time out on large downloads. Solutions:
- Retry: the downloader is idempotent (re-downloads missing files)
- Use Method C (curl-based parallel download) for more control
- Use Method D (synthetic data) if internet is completely unavailable

### mProjExec fails with "No overlap with output area"

Some downloaded images may not overlap with the target `region.hdr`. This is
normal — mProjExec skips non-overlapping images. Check that at least 80% of
images are successfully projected:

```bash
grep -c "proj" results/*/slurm_*.out  # count projected images
```

### Tmpfs runs out of space

If intermediate data exceeds `/dev/shm` capacity, the tmpfs configuration will
fail. This is expected and should be recorded as a FAILED result — it
demonstrates that storage selection matters (DPM would avoid this config).

### Montage compilation fails

```bash
cd "${MONTAGE_SRC}"
# Common fix: JPEG library issue
sed -i 's/#define DONT_USE_B_MODE 1/\/* #undef DONT_USE_B_MODE *\//' \
  lib/src/jpeg-8b/jconfig.h
make clean && make
```

### Per-stage timing shows 0 or negative values

The timing uses `date +%s.%N`. If `%N` is not supported (some minimal shells),
fall back to integer seconds:

```bash
# In run_montage.sh, replace:
#   T_START=$(date +%s.%N)
# with:
#   T_START=$(date +%s)
```

---

## What Success Looks Like

After all 27 jobs complete, `results/all_results.csv` should show:

| size  | backend | nodes | total_time_s | n_images | n_pairs | status  |
|-------|---------|-------|-------------|----------|---------|---------|
| large | ssd     | 4     | ~Xs         | 1425     | ~3500   | SUCCESS |
| large | ssd     | 8     | ~Xs         | 1425     | ~3500   | SUCCESS |
| large | ssd     | 16    | ~Xs         | 1425     | ~3500   | SUCCESS |
| large | beegfs  | 4     | ~Xs         | 1425     | ~3500   | SUCCESS |
| large | beegfs  | 8     | ~Xs         | 1425     | ~3500   | SUCCESS |
| large | beegfs  | 16    | ~Xs         | 1425     | ~3500   | SUCCESS |
| large | tmpfs   | 4     | ~Xs         | 1425     | ~3500   | SUCCESS or FAILED |
| large | tmpfs   | 8     | ~Xs         | 1425     | ~3500   | SUCCESS or FAILED |
| large | tmpfs   | 16    | ~Xs         | 1425     | ~3500   | SUCCESS or FAILED |

Key observations to report:
1. Runtime varies significantly across storage backends (validates DPM relevance)
2. Increasing nodes reduces runtime for parallel stages (validates parallelism dimension)
3. Tmpfs may fail for large data (validates storage capacity as a selection factor)
4. DPM rank deviation should be within 5% for most producer-consumer pairs
