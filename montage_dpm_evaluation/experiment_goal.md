# Montage DPM Evaluation: Experiment Goal

## Motivation

Reviewers identified a critical gap: the DPM paper evaluates only three workflows (1000 Genomes, PyflexTRKR, DeepDriveMD), and only 1000 Genomes is truly data-intensive (>10 GB intermediate data). Reviewer A questioned scalability with only 9 configurations; Reviewer B asked for evaluation on diverse workflow topologies; Reviewer D found the advantage "less conclusive" for PyflexTRKR and DeepDriveMD. Adding a 4th workflow with large I/O volume and a fundamentally different DAG structure strengthens DPM's generalizability claims.

Luke (IIT co-author) directly recommended: "Add one more data-intensive workflow evaluation."

## Why Montage

**Montage** (astronomical image mosaicking) is a well-established HPC benchmark workflow used extensively by the Pegasus team and the workflow scheduling community. It provides:

1. **Truly data-intensive I/O** — A 6-degree 2MASS J-band mosaic involves ~1,425 FITS images (~6.3 GB raw), generating ~28 GB of intermediate data across reprojection, differencing, and background correction stages. This exceeds 1000 Genomes' data volume.

2. **Unique DAG structure** — Unlike the existing 3 workflows, Montage has a data-dependent fan-out pattern: N input images produce O(N×k) overlap pairs, creating a variable-width parallel stage that depends on image geometry. This is fundamentally different from the fixed parallelism in 1000 Genomes (300 tasks), PyflexTRKR (96 tasks), or DeepDriveMD (12 tasks).

3. **Different I/O pattern** — Large FITS file reads/writes with write amplification (raw → projected → differences → corrected → mosaic). The pipeline is both read-heavy (mDiffExec reads 2 images per pair) and write-heavy (generates difference images for every overlap).

4. **Different scientific domain** — Astronomy, adding to genomics (1KG), climate (PyflexTRKR), and ML+MD (DeepDriveMD).

5. **Already validated** — Successfully compiled and executed on the Ares cluster with Darshan I/O tracing.

## What This Experiment Demonstrates

### Q1: Does DPM correctly rank storage-parallelism configurations for a data-intensive image processing workflow?

**Method:**
- Run the full 10-stage Montage pipeline on a 2MASS J-band mosaic across:
  - 3 storage backends: BeeGFS, local SSD, tmpfs (where data fits)
  - 3 node counts: 4, 8, 16 nodes (controlling task parallelism for mProjExec, mDiffExec, mBgExec)
  - = 9 configurations (matching 1000 Genomes and PyflexTRKR structure)
- Profile I/O with Datalife to capture per-stage producer-consumer transfer patterns
- Compute DPM scores offline from existing IOR profiling data
- Compare DPM's predicted ranking against measured runtime ranking

**Success criterion:** DPM rank deviation within 5% for the majority of producer-consumer pairs.

### Q2: Does DPM provide meaningful speedup over baseline scheduling for image workflows?

**Method:**
- Compare DPM-selected configuration against baseline approaches:
  - dagP: compute-centric partitioning (BeeGFS, max nodes)
  - DFMan: bandwidth-maximization (fastest single-task storage)
  - FaaSFlow: data-locality-first (co-locate on same nodes)
- Report end-to-end workflow runtime for each approach

**Success criterion:** DPM achieves measurable speedup, demonstrating that storage-parallelism optimization matters for image processing workflows.

## How Results Map to Paper Claims

| Paper Claim | Evidence from This Experiment |
|---|---|
| DPM generalizes beyond 3 workflows | Correct ranking on a 4th workflow with different DAG structure |
| DPM handles data-intensive workloads | ~28 GB intermediate data, larger than any existing evaluation |
| DPM works across scientific domains | Astronomy joins genomics, climate, ML+MD |
| Storage selection matters for workflow I/O | Measurable runtime difference across storage backends |
| DPM's surrogate model is accurate | Rank deviation within 5% on Montage producer-consumer pairs |

## Data Source

### Real 2MASS Data (used for pipeline validation)

**Survey:** 2MASS J-band (Two Micron All Sky Survey, near-infrared)
**Region:** Galactic plane near M17 (RA≈275.2°, Dec≈-16.17°) — dense stellar field with high image overlap
**Download:** Montage's built-in `mArchiveDownload` from IRSA (https://irsa.ipac.caltech.edu)

| Scale | Region Size | Images | Dimensions | Raw Data | Intermediate | Overlap Pairs |
|---|---|---|---|---|---|---|
| small | 2° | 208 | 512×1024 | 0.3 GB | ~1 GB | ~1,022 |
| medium | 4° | 733 | 512×1024 | 1.2 GB | ~3.8 GB | ~3,372 |
| large | 6° | 1,425 | 512×1024 | 2.3 GB | ~7.4 GB | ~5,726 |

### Synthetic Data (used for DPM I/O evaluation)

Real 2MASS images are small (~1.5 MB each), producing only ~7 GB intermediate data at the
largest scale — insufficient to stress storage tiers for DPM evaluation. Synthetic FITS
images with larger pixel dimensions produce the same Montage I/O patterns (reprojection,
differencing, background correction) at controllable data volumes.

**Generation method:** 208 synthetic FITS files with valid WCS headers (RA-TAN/DEC-TAN
gnomonic projection) placed in a 6° grid around M17 (RA=275.196°, Dec=-16.172°). Each
image contains random Gaussian noise (mean=100, std=10) in float32 big-endian format per
FITS standard. The WCS headers ensure proper overlap for Montage's pair detection.

```bash
# Generation command (from montage_dpm_evaluation/ directory):
python3 scripts/generate_synthetic_fits.py --n-images 208 --size synth_small  # 2048×2048
python3 scripts/generate_synthetic_fits.py --n-images 208 --size synth_medium # 4096×4096
python3 scripts/generate_synthetic_fits.py --n-images 208 --size synth_large  # 8192×8192
```

| Scale | Images | Dimensions | Raw Data | Est. Intermediate | mProject time/image |
|---|---|---|---|---|---|
| synth_small | 208 | 2048×2048 | 3.2 GB | ~13 GB | ~24s |
| synth_medium | 208 | 4096×4096 | 13.0 GB | ~50 GB | ~96s |
| synth_large | 208 | 8192×8192 | 52.0 GB | ~200 GB | ~6 min |

**Why synthetic data is valid for DPM evaluation:** DPM evaluates I/O performance, not
scientific correctness. Synthetic images produce identical Montage I/O patterns (same file
formats, same pipeline stages, same parallel task counts) as real data. The pixel values
(random noise vs real astronomical signal) do not affect file sizes, read/write patterns,
or storage tier performance. Montage processes each FITS image identically regardless of
content.

**Fixed parallelism:** All synthetic datasets use 208 images to maintain consistent task
counts across scales. This isolates the I/O volume variable — the number of parallel
mProject/mBackground tasks is always 208, only the per-task data size changes.

The **synth_large** configuration (208 images × 8192×8192 × 4 bytes = 52 GB raw, ~200 GB
intermediate) is the primary DPM evaluation target, comparable to WfBench's data volumes.

## Experiment Scope

- **Data:** synth_medium (208 synthetic FITS @ 4096×4096, 13 GB raw, ~130 GB total I/O)
- **Storage backends:** BeeGFS (shared), local NVMe SSD (node-local with staging), tmpfs (RAM-backed, node-local with staging)
- **Node scales:** 4, 8, 16 nodes (fixed 208 images, varying parallelism per node)
- **Task distribution:** Individual mProject/mDiff/mBackground calls via srun, 64 tasks/node
- **Configurations:** 9 (3 storage × 3 node counts), fixed data size
- **Cluster:** PNNL Deception (64-core AMD, 251 GB RAM, BeeGFS + 477 GB NVMe SSD per node)

## Producer-Consumer Structure for DPM

Montage's 10-stage pipeline maps to 5 producer-consumer pairs for DPM analysis:

| Pair | Producer Stage | Consumer Stage | Data Flow |
|---|---|---|---|
| 1 | mProject (reprojection) | mDiff (differencing) | Projected FITS → read pairs for overlap computation |
| 2 | mDiff (differencing) | mFitExec (plane fitting) | Difference FITS → statistical fitting |
| 3 | mFitExec → mBgModel (modeling) | mBackground (correction) | Correction params → apply to projected images |
| 4 | mProject (reprojection) | mBackground (correction) | Projected FITS → background-corrected FITS |
| 5 | mBackground (correction) | mAdd (coaddition) | Corrected FITS → final mosaic |

## I/O Volume Analysis

**Important:** The "intermediate data size" reported in results (`total_intermediate_bytes`)
is the **peak on-disk footprint** — the sum of all intermediate files that exist on storage
simultaneously. The **total I/O volume** (all reads + writes) is significantly larger because
each file is written once and then read one or more times by downstream stages.

### Per-stage I/O breakdown (N = number of images, P = number of overlap pairs)

| Stage | Writes | Reads | Notes |
|---|---|---|---|
| mProject | N projected FITS (1× each) | N raw FITS (1× each) | Heaviest compute + I/O stage |
| mDiff | P diff FITS (1× each) | 2P projected reads (each pair reads 2 images) | Read amplification: 2× |
| mFitExec | 1 fits.tbl | P diff FITS (1× each) | Light I/O |
| mBgModel | 1 corrections.tbl | fits.tbl + proj_images.tbl | Negligible I/O |
| mBackground | N corrected FITS (1× each) | N projected FITS (1× each) + corrections.tbl | Projected FITS read a 2nd time |
| mAdd | 1 mosaic FITS | N corrected FITS (1× each) | Serial, read-heavy |

### Read amplification

Projected FITS files are **read 3 times total**:
1. By mDiff (2 reads per pair, but each image appears in multiple pairs)
2. By mBackground (1 read per image)

For 208 images with ~1022 pairs, each projected image appears in ~10 pairs on average,
so mDiff reads ~2044 projected files total (10× the file count).

### Estimated total I/O volume by dataset

| Dataset | Peak on-disk | Total writes | Total reads | **Total I/O** | Amplification |
|---|---|---|---|---|---|
| real small (512×1024) | 1.0 GB | ~1.0 GB | ~1.6 GB | **~2.6 GB** | 2.6× |
| synth_small (2048²) | ~13 GB | ~13 GB | ~21 GB | **~34 GB** | 2.6× |
| synth_medium (4096²) | ~50 GB | ~50 GB | ~80 GB | **~130 GB** | 2.6× |
| synth_large (8192²) | ~200 GB | ~200 GB | ~320 GB | **~520 GB** | 2.6× |

The ~2.6× amplification factor comes from the DAG structure: data flows through multiple
stages with fan-out at the differencing step. This is characteristic of image mosaicking
workflows and distinct from the linear pipeline pattern in WfBench.

**For DPM evaluation:** The total I/O volume (~130 GB for synth_medium) is what determines
storage tier impact. The read amplification means storage read bandwidth is tested more
heavily than write bandwidth, unlike WfBench which has balanced read/write.

## Paper Placement

Results go in **Section 5** as a new workflow subsection (parallel to 1000 Genomes, PyflexTRKR, DeepDriveMD) with:
- Workflow I/O characteristics table (matching existing io_1kg.tex, io_pyflex.tex, io_ddmd.tex format)
- DPM rank deviation figure
- Row in the workflow runtime comparison figure
- DPM analysis time measurement
