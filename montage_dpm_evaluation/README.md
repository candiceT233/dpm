# Montage DPM Evaluation

> **New here? Start with [SETUP_AGENT.md](SETUP_AGENT.md).** It is a fully
> self-contained, step-by-step guide that takes a fresh HPC account from
> "nothing installed" to "27 jobs submitted and analyzed" — including
> compiling Montage from source, downloading the input dataset from IRSA, and
> running the full pipeline. The rest of this README is a quick reference for
> people who have already run that setup once.

## Purpose

This experiment adds Montage (astronomical image mosaicking) as a 4th workflow
to the DPM paper evaluation, addressing reviewer concerns about narrow evaluation
scope and insufficient data intensity. Montage provides:

- **Large I/O volume**: ~28 GB intermediate data (6° 2MASS mosaic, 1,425 images)
- **Unique DAG structure**: data-dependent fan-out (N images → O(N×k) overlap pairs)
- **Different scientific domain**: astronomy (joins genomics, climate, ML+MD)

## Folder Structure

```
montage_dpm_evaluation/
├── README.md                    # This file
├── experiment_goal.md           # Detailed experiment motivation and goals
├── config.env.template          # Cluster-specific config (copy to config.env)
├── design/
│   ├── workflow_design.md       # Montage pipeline stages and I/O patterns
│   └── experiment_matrix.md     # All configurations to test (9 configs × 3 runs)
├── SETUP_AGENT.md               # Full from-scratch installation + run guide
├── scripts/
│   ├── setup_env.sh             # Verify env (Montage, Python, storage paths)
│   ├── download_data.sh         # Download 2MASS FITS images from IRSA
│   ├── run_montage.sh           # Run Montage pipeline for one configuration
│   ├── run_all_configs.sh       # Submit all 27 jobs
│   ├── collect_results.sh       # Aggregate results into CSV
│   └── analyze_io_time.sh       # Per-stage I/O % via strace (small dataset)
├── analysis/
│   └── compare_results.py       # Produce ranking tables and plots
├── data/                        # Downloaded FITS images (not in git)
│   ├── small/raw_images/        # ~100 images, ~0.4 GB
│   ├── medium/raw_images/       # ~400 images, ~1.8 GB
│   └── large/raw_images/        # ~1,425 images, ~6.3 GB
└── results/                     # Experiment outputs (not in git)
```

## Quick Start (after first-time install)

This assumes Montage is already compiled and `config.env` is filled in. If
either is not true, follow [SETUP_AGENT.md](SETUP_AGENT.md) instead.

```bash
# Pin the working directory so paths below don't depend on where you cd from
export ROOT_DIR="$(pwd)"

# 1. Configure for your cluster (one-time)
cp config.env.template config.env
# Edit config.env: partition, account, storage paths, MONTAGE_BIN, MONTAGE_PY,
# PYTHON_ENV, and (optional) DARSHAN_LIB / DARSHAN_LOG_DIR.

# 2. Verify environment
bash scripts/setup_env.sh

# 3. Download 2MASS data (large = 6-degree field, ~1425 images, ~6.3 GB)
bash scripts/download_data.sh --size large

# 4. Run single test
bash scripts/run_montage.sh --size large --storage ssd --nodes 4

# 5. Run all 27 jobs (9 configs × 3 runs)
bash scripts/run_all_configs.sh --size large

# 6. Collect and analyze
bash scripts/collect_results.sh
python analysis/compare_results.py --results results/all_results.csv
```

## Scripts Reference

Every script reads `config.env` from the folder root, so the values you set
there (partition, account, storage paths, `MONTAGE_BIN`, `MONTAGE_PY`, …)
flow through to all of them. Run scripts from any working directory — they
resolve their own location.

### `scripts/setup_env.sh` — verify the environment

Checks Montage binaries, MontagePy (for the IRSA download), Python packages,
and the three storage paths (`LOCAL_SSD_PATH`, `BEEGFS_PATH`, `TMPFS_PATH`).
Creates `${ROOT_DIR}/.venv` if `PYTHON_ENV` isn't already populated. Safe to
re-run.

```bash
bash scripts/setup_env.sh
```

- **Reads:** `config.env`
- **Writes:** `${ROOT_DIR}/.venv/` (only if `PYTHON_ENV` is unset/missing)
- **Run when:** after editing `config.env`, after rebuilding Montage, or
  whenever a job fails with "binary not found".

### `scripts/download_data.sh` — fetch 2MASS FITS data from IRSA

Calls `mArchiveDownload` (from MontagePy) to pull a 2-, 4-, or 6-degree field
of view around M17, then generates the matching `region.hdr` mosaic header.

```bash
bash scripts/download_data.sh --size small      # ~100 images, ~0.4 GB,  2°
bash scripts/download_data.sh --size medium     # ~400 images, ~1.8 GB,  4°
bash scripts/download_data.sh --size large      # ~1425 images, ~6.3 GB, 6°
```

- **Reads:** `MONTAGE_PY` from `config.env`
- **Writes:** `data/<size>/raw_images/*.fits` and `data/<size>/region.hdr`
- **Internet:** required (reaches `irsa.ipac.caltech.edu`)
- **Idempotent:** re-running re-downloads only missing files
- **If it fails:** see SETUP_AGENT.md Step 3 for Methods C (curl) and D
  (synthetic FITS) fallbacks.

### `scripts/run_montage.sh` — run one Montage pipeline configuration

Submits one Slurm job that runs the full 10-stage Montage pipeline on the
chosen storage backend and node count. Writes per-stage timings + intermediate
data sizes into `results/<run_id>/result.txt`.

```bash
bash scripts/run_montage.sh --size large --storage ssd    --nodes 4
bash scripts/run_montage.sh --size large --storage beegfs --nodes 8
bash scripts/run_montage.sh --size large --storage tmpfs  --nodes 16
```

- **Args:** `--size {small|medium|large}` `--storage {ssd|beegfs|tmpfs}` `--nodes {4|8|16}`
- **Reads:** `data/<size>/raw_images/`, `data/<size>/region.hdr`, `config.env`
- **Writes:** `results/<storage>_<size>_<nodes>n_<timestamp>/`
  containing `job_montage.sh`, `slurm_<jobid>.{out,err}`, `result.txt`
- **Storage semantics:**
  - `beegfs` — all I/O on the shared parallel FS
  - `ssd` / `tmpfs` — heavy stages (mProject, mBackground) run on per-node
    local storage with explicit stage-in / stage-out timed separately
- **If `DARSHAN_LIB` is set:** Darshan logs land in `${DARSHAN_LOG_DIR}/YYYY/M/D/`
  (defaults to `results/darshan-logs/...`).

### `scripts/run_all_configs.sh` — submit the full sweep (3 × 3 × 3 = 27 jobs)

Loops over `{ssd, beegfs, tmpfs} × {4, 8, 16 nodes} × 3 runs`, calling
`run_montage.sh` for each. Use `--dry-run` first to preview the commands
without submitting.

```bash
bash scripts/run_all_configs.sh --size large --dry-run    # preview
bash scripts/run_all_configs.sh --size large              # submit all 27
```

- **Args:** `--size {small|medium|large}`, `--dry-run` (optional)
- **Throttle:** 2 s between submissions to avoid hammering the scheduler
- **Monitor:** `squeue --me`

### `scripts/collect_results.sh` — aggregate per-run results into one CSV

Walks every `results/*/result.txt`, parses the `key=value` lines, and writes
a wide CSV with one row per run (per-stage timings + intermediate sizes +
status). Prints the table in column-aligned form.

```bash
bash scripts/collect_results.sh
bash scripts/collect_results.sh --output results/my_run.csv
```

- **Reads:** `results/*/result.txt`
- **Writes:** `results/all_results.csv` (default) or the path given by `--output`
- **Run when:** all (or enough) jobs in the sweep have finished.

### `scripts/analyze_io_time.sh` — per-stage I/O fraction via strace

Runs each Montage stage on the **small** dataset under
`strace -f -T -e trace=<I/O syscalls>` and reports wall time, total syscall
time, and I/O percentage. Used to characterize how I/O-bound each stage is —
this is the data behind the "Montage per-stage I/O time analysis" commit.

```bash
bash scripts/analyze_io_time.sh > io_analysis.log
```

- **Prereq:** `data/small/` already downloaded (`download_data.sh --size small`)
- **Output:** stdout, one line per stage; redirect to a file as shown
- **Cost:** runs on the login/current node, single-process — no Slurm submission

### `analysis/compare_results.py` — ranking + plots

Reads the CSV from `collect_results.sh`, drops failed runs, and produces
per-(size, nodes) ranking tables and a runtime bar chart.

```bash
source "${PYTHON_ENV:-${ROOT_DIR}/.venv}/bin/activate"
python analysis/compare_results.py --results results/all_results.csv
```

- **Reads:** the CSV produced by `collect_results.sh`
- **Writes:** ranking table to stdout; figures to the same directory as the CSV
- **Deps:** `numpy`, `pandas`, `matplotlib` (installed by `setup_env.sh`)

### Typical end-to-end flow

```bash
export ROOT_DIR="$(pwd)"
bash scripts/setup_env.sh                         # 1. verify
bash scripts/download_data.sh --size small        # 2a. small first (smoke test)
bash scripts/run_montage.sh --size small --storage ssd --nodes 4
                                                  #     wait for SUCCESS
bash scripts/download_data.sh --size large        # 2b. then full dataset
bash scripts/run_all_configs.sh --size large --dry-run
bash scripts/run_all_configs.sh --size large     # 3. submit 27 jobs
                                                  #    wait for queue to drain
bash scripts/collect_results.sh                   # 4. aggregate
python analysis/compare_results.py --results results/all_results.csv  # 5. analyze
```

## Configuration Matrix

| Storage | 4 nodes | 8 nodes | 16 nodes |
|---------|---------|---------|----------|
| BeeGFS  | Run 01  | Run 02  | Run 03   |
| SSD     | Run 04  | Run 05  | Run 06   |
| Tmpfs   | Run 07  | Run 08  | Run 09   |

Each configuration is run 3 times for statistical significance.

## Dependencies

- Montage C toolkit, compiled from source — see SETUP_AGENT.md Step 2
  (no external runtime deps; needs `gcc` and `make` to build)
- Python >= 3.8 with `numpy`, `pandas`, `matplotlib` — installed into a
  virtualenv at `${ROOT_DIR}/.venv` by default
- Slurm (`sbatch`, `srun`, `scontrol`) on the cluster
- Three storage tiers reachable from compute nodes: node-local SSD, shared
  parallel FS (BeeGFS / Lustre / GPFS), and tmpfs (`/dev/shm`)
- Internet access on at least one node for data download (IRSA archive)
- Optional: Darshan for I/O tracing, Datalife for profiling
