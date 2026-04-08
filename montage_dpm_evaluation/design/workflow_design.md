# Montage Workflow Design for DPM Evaluation

## Workflow Overview

Montage is a 10-stage astronomical image mosaicking pipeline that assembles
FITS images from sky surveys into seamless mosaics. The pipeline has a clear
producer-consumer structure with both embarrassingly parallel and serial stages.

## Pipeline Stages

```
Raw FITS images
    │
    ▼
[1] mImgtbl ──────────── Extract image metadata (O(N), serial)
    │
    ▼
[2] mProjExec ────────── Reproject all images to common frame (O(N), parallel per image)
    │
    ▼
[3] mImgtbl ──────────── Re-catalog projected images (O(N), serial)
    │
    ▼
[4] mOverlaps ────────── Identify overlapping pairs (O(N²) worst case, serial)
    │
    ▼
[5] mDiffExec ────────── Compute difference images per pair (O(pairs), parallel per pair)
    │
    ▼
[6] mFitExec ─────────── Fit planes to differences (O(pairs), parallel per pair)
    │
    ▼
[7] mBgModel ─────────── Model global background corrections (O(N), serial)
    │
    ▼
[8] mBgExec ──────────── Apply corrections to projected images (O(N), parallel per image)
    │
    ▼
[9] mImgtbl ──────────── Re-catalog corrected images (O(N), serial)
    │
    ▼
[10] mAdd ────────────── Co-add into final mosaic (O(N × pixels), serial)
```

## I/O Characteristics

| Stage | I/O Type | Read Pattern | Write Pattern | Data Volume |
|-------|----------|-------------|---------------|-------------|
| mProjExec | Producer | Sequential read raw FITS | Sequential write projected FITS | N × image_size |
| mDiffExec | Consumer/Producer | Read 2 projected FITS per pair | Write 1 diff FITS per pair | pairs × overlap_size |
| mFitExec | Consumer | Read diff FITS | Write fit params (small) | pairs × small |
| mBgExec | Consumer/Producer | Read projected FITS + corrections | Write corrected FITS | N × image_size |
| mAdd | Consumer | Read all corrected FITS | Write 1 mosaic FITS | N × image_size → 1 mosaic |

## Producer-Consumer Pairs for DPM

| Pair | Producer | Consumer | Key I/O |
|------|----------|----------|---------|
| P1 | mProjExec | mDiffExec | Projected → overlap differencing |
| P2 | mDiffExec | mFitExec | Differences → plane fitting |
| P3 | mBgModel | mBgExec | Correction params → apply to images |
| P4 | mProjExec | mBgExec | Projected images → background correction |
| P5 | mBgExec | mAdd | Corrected images → final mosaic |

## Parallelism Structure

**Parallel stages** (controlled by node count / tasks-per-node):
- mProjExec: 1 task per input image → N parallel tasks
- mDiffExec: 1 task per overlap pair → ~N×k/2 parallel tasks
- mFitExec: 1 task per overlap pair → ~N×k/2 parallel tasks
- mBgExec: 1 task per image → N parallel tasks

**Serial stages** (cannot be parallelized):
- mImgtbl: metadata extraction (fast)
- mOverlaps: geometric computation (fast)
- mBgModel: global optimization (fast)
- mAdd: final coaddition (I/O bound on reads)

## Data Scaling (2MASS J-band, M17 region)

| Scale | Region | Images (N) | Est. Pairs | Raw Data | Intermediate |
|-------|--------|-----------|-----------|----------|-------------|
| small | 2° | ~100 | ~250 | ~0.4 GB | ~2 GB |
| medium | 4° | ~400 | ~1,000 | ~1.8 GB | ~8 GB |
| large | 6° | ~1,425 | ~3,500 | ~6.3 GB | ~28 GB |

Each 2MASS atlas image is ~4-5 MB decompressed.
Intermediate data includes: projected/ + diffs/ + corrected/ ≈ 4-5× raw.
