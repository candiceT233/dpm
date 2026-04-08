# Experiment Matrix

## Evaluation Goal

Validate that DPM's predicted storage-parallelism ranking matches actual
measured runtime for the Montage workflow, following the same evaluation
pattern as 1000 Genomes (9 configs) and PyflexTRKR (9 configs).

## Fixed Variables

| Variable | Value | Notes |
|----------|-------|-------|
| Survey | 2MASS J-band | M17 region (galactic plane, dense overlap) |
| Data scale | large (6° region) | ~1,425 images, ~6.3 GB raw, ~28 GB intermediate |
| Runs per config | 3 | For mean ± std dev |
| Pipeline | Full 10-stage Montage | mImgtbl → mProjExec → ... → mAdd |

## Primary Evaluation: DPM Ranking Validation (9 configs)

Matches 1000 Genomes and PyflexTRKR structure: 3 storage × 3 parallelism.

| Run ID | Storage | Nodes | Parallelism | Expected DPM Rank | Priority |
|--------|---------|-------|-------------|-------------------|----------|
| 01 | BeeGFS | 4 | Low | TBD | High |
| 02 | BeeGFS | 8 | Medium | TBD | High |
| 03 | BeeGFS | 16 | High | TBD | High |
| 04 | Local SSD | 4 | Low | TBD | High |
| 05 | Local SSD | 8 | Medium | TBD | High |
| 06 | Local SSD | 16 | High | TBD | High |
| 07 | Tmpfs | 4 | Low | TBD (may fail: data > tmpfs capacity) | High |
| 08 | Tmpfs | 8 | Medium | TBD (may fail) | High |
| 09 | Tmpfs | 16 | High | TBD (may fit with enough nodes) | Medium |

> Note: Tmpfs configs may fail if intermediate data exceeds /dev/shm capacity.
> On 384 GB nodes, tmpfs is typically ~63 GB. With ~28 GB intermediate data
> distributed across 16 nodes (~1.75 GB/node), tmpfs may be feasible at high
> parallelism. At 4 nodes (~7 GB/node), it should also fit.
> However, the working set includes projected + diffs + corrected copies,
> so actual per-node usage depends on task distribution.

**Total: 9 configs × 3 runs = 27 jobs**

## Parallelism Rationale

Node counts chosen to match existing workflow evaluation patterns:

| Workflow | Node Counts | Why |
|----------|------------|-----|
| 1000 Genomes | 2, 5, 10 | 10-chromosome pipeline, 300 parallel indiv tasks |
| PyflexTRKR | 4, 8, 16 | 96 concurrent tasks per stage |
| DeepDriveMD | 2, 4 | 12 simulation tasks |
| **Montage** | **4, 8, 16** | **~1,425 images to reproject + ~3,500 diff pairs** |

Montage's parallel stages (mProjExec, mDiffExec, mBgExec) scale with node count.
At 4 nodes: ~356 images/node for reprojection, ~875 pairs/node for differencing.
At 16 nodes: ~89 images/node, ~219 pairs/node.

## Baseline Comparison

For the workflow runtime comparison figure, run additional configs:

| Baseline | Storage | Nodes | Description |
|----------|---------|-------|-------------|
| dagP | BeeGFS | 16 | Max parallelism, shared FS (compute-centric) |
| DFMan | SSD | 16 | Fastest local storage (bandwidth-maximization) |
| FaaSFlow | SSD | 4 | Co-locate on fewer nodes (data-locality) |

**Additional: 3 baselines × 3 runs = 9 jobs**

## Total

| Phase | Jobs | Description |
|-------|------|-------------|
| DPM ranking | 27 | 9 configs × 3 runs |
| Baselines | 9 | 3 baselines × 3 runs |
| **Total** | **36** | |

## Minimum Viable Result

| Priority | Configs | What it shows |
|----------|---------|---------------|
| Must have | 01-06 (BeeGFS + SSD × 3 nodes) | DPM ranking correct for 2 storage tiers × 3 parallelism |
| Should have | 07-09 (Tmpfs) | Complete 9-config grid |
| Nice to have | Baselines | Speedup comparison for paper figure |

**Minimum: 6 configs × 3 runs = 18 jobs**
