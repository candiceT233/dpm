# Montage DPM Evaluation

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
├── scripts/
│   ├── setup_env.sh             # One-time environment setup
│   ├── download_data.sh         # Download 2MASS FITS images from IRSA
│   ├── run_montage.sh           # Run Montage pipeline for one configuration
│   ├── run_all_configs.sh       # Submit all 27 jobs
│   └── collect_results.sh       # Aggregate results into CSV
├── analysis/
│   └── compare_results.py       # Produce ranking tables and plots
├── data/                        # Downloaded FITS images (not in git)
│   ├── small/raw_images/        # ~100 images, ~0.4 GB
│   ├── medium/raw_images/       # ~400 images, ~1.8 GB
│   └── large/raw_images/        # ~1,425 images, ~6.3 GB
└── results/                     # Experiment outputs (not in git)
```

## Quick Start

```bash
# 1. Configure for your cluster
cp config.env.template config.env
# Edit config.env with cluster paths, partitions, Montage binary location

# 2. Set up environment
bash scripts/setup_env.sh

# 3. Download 2MASS data (large = 6-degree field, ~1425 images)
bash scripts/download_data.sh --size large

# 4. Run single test
bash scripts/run_montage.sh --size large --storage ssd --nodes 4

# 5. Run all 27 jobs (9 configs × 3 runs)
bash scripts/run_all_configs.sh --size large

# 6. Collect and analyze
bash scripts/collect_results.sh
python analysis/compare_results.py --results results/all_results.csv
```

## Configuration Matrix

| Storage | 4 nodes | 8 nodes | 16 nodes |
|---------|---------|---------|----------|
| BeeGFS  | Run 01  | Run 02  | Run 03   |
| SSD     | Run 04  | Run 05  | Run 06   |
| Tmpfs   | Run 07  | Run 08  | Run 09   |

Each configuration is run 3 times for statistical significance.

## Dependencies

- Montage C toolkit (compiled from source)
- Python >= 3.8 (numpy, pandas, matplotlib)
- Access to cluster storage: local SSD, TMPFS, BeeGFS
- Internet access for data download (IRSA archive)
- Optional: Darshan for I/O tracing, Datalife for profiling
