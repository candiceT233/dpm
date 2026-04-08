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

**Survey:** 2MASS J-band (Two Micron All Sky Survey, near-infrared)
**Region:** Galactic plane near M17 (RA≈275.2°, Dec≈-16.17°) — dense stellar field with high image overlap
**Download:** Montage's built-in `mArchiveDownload` from IRSA (https://irsa.ipac.caltech.edu)

| Scale | Region Size | Images | Raw Data | Est. Intermediate | Est. Overlap Pairs |
|---|---|---|---|---|---|
| small | 2° | ~100 | ~0.4 GB | ~2 GB | ~250 |
| medium | 4° | ~400 | ~1.8 GB | ~8 GB | ~1,000 |
| large | 6° | ~1,425 | ~6.3 GB | ~28 GB | ~3,500 |

The **large** configuration is the primary evaluation target. Small and medium are for validating the pipeline and for DPM ranking comparison across data sizes.

## Experiment Scope

- **Configurations:** 9 (3 storage × 3 node counts) for the large dataset
- **Repetitions:** 3 runs per configuration for statistical significance
- **Total jobs:** 27 (minimum viable) + optional small/medium validation
- **Cluster:** Same 96-node cluster as existing evaluations (dual AMD EPYC 7502, 384 GB RAM)

## Producer-Consumer Structure for DPM

Montage's 10-stage pipeline maps to 5 producer-consumer pairs for DPM analysis:

| Pair | Producer Stage | Consumer Stage | Data Flow |
|---|---|---|---|
| 1 | mProjExec (reprojection) | mDiffExec (differencing) | Projected FITS → read pairs for overlap computation |
| 2 | mDiffExec (differencing) | mFitExec (plane fitting) | Difference FITS → statistical fitting |
| 3 | mFitExec → mBgModel (modeling) | mBgExec (correction) | Correction params → apply to projected images |
| 4 | mProjExec (reprojection) | mBgExec (correction) | Projected FITS → background-corrected FITS |
| 5 | mBgExec (correction) | mAdd (coaddition) | Corrected FITS → final mosaic |

## Paper Placement

Results go in **Section 5** as a new workflow subsection (parallel to 1000 Genomes, PyflexTRKR, DeepDriveMD) with:
- Workflow I/O characteristics table (matching existing io_1kg.tex, io_pyflex.tex, io_ddmd.tex format)
- DPM rank deviation figure
- Row in the workflow runtime comparison figure
- DPM analysis time measurement
