# DPM Evaluation — Job Completion Tracker

**Updated:** 2026-04-08 18:10 PDT

## What's needed to start writing

| Experiment | Configs | Status | ETA |
|-----------|---------|--------|-----|
| WfBench BeeGFS (8n, 16n) × small/med/large | 6 | 4 done, 1 running, 1 pending | ~3h |
| WfBench DPM mixed (8n, 16n) × small/med/large | 6 | 0 done, 6 pending (after BeeGFS) | ~5h |
| WfBench SSD w/ scp staging (8n, 16n) × s/m/l | 6 | 0 done, 6 running | ~1h |
| WfBench tmpfs w/ scp staging (8n, 16n) × s/m/l | 6 | 0 done, 3 running, 3 pending | ~1h |
| ADIOS SST fair (8n, 16n) × small/med/large | 6 | 1 done, 5 running | ~2h |
| Montage synth_small × beegfs/ssd/tmpfs × 4/8/16n | 9 | 1 done, 8 pending | ~7h |
| **Total** | **39** | **6 done** | |

**Est. completion:** Chain A (BeeGFS + dpm_mixed) ~Apr 9, 02:00 AM. Node-local jobs ~tonight.

## Completed — WfBench BeeGFS (Chain A)

| Job ID | Config | Elapsed |
|--------|--------|---------|
| 639318 | beegfs_small_8n | 2:38 |
| 639320 | beegfs_medium_8n | 16:39 |
| 639322 | beegfs_large_8n | 1:25:55 |
| 639324 | beegfs_small_16n | 5:03 |
| 639326 | beegfs_medium_16n | 33:57 |

## Completed — ADIOS SST fair (no computation, BP5 output + ADIOS aggregation)

| Job ID | Config | Stage 1+2 | Stage 3 | Total | Status |
|--------|--------|-----------|---------|-------|--------|
| 640636 | adios_small_8n | 265s | 541s | **806s (13:26)** | SUCCESS |
| 640642 | adios_small_16n | 262s | 950s | **1212s (20:21)** | SUCCESS |

## Completed — WfBench tmpfs w/ scp staging

| Job ID | Config | Stage1 | scp 1→2 | Stage2 | scp 2→3 | Total | Status |
|--------|--------|--------|---------|--------|---------|-------|--------|
| 640652 | tmpfs_small_8n | 9s | 258s | 11s | 222s | **515s** | SUCCESS (scp=93%) |
| 640656 | tmpfs_medium_8n | 46s | 10s | 0s | 17s | 73s | **FAILED** (24/32 — tmpfs OOM) |
| 640660 | tmpfs_large_8n | 53s | 9s | 1s | 14s | 77s | **FAILED** (32/32 — tmpfs OOM) |

## Completed — Montage synth_small

| Job ID | Config | Elapsed | Intermediate |
|--------|--------|---------|-------------|
| 639696 | beegfs_synth_small_4n | 47:30 | 30.7 GB |

## Currently Running

| Job ID | Config | Elapsed | Notes |
|--------|--------|---------|-------|
| **Chain A (sequential)** | | | |
| 639328 | beegfs_large_16n | 22 min | est. ~2h |
| **ADIOS fair rerun (parallel)** | | | |
| 640638 | adios_medium_8n | 14 min | |
| 640640 | adios_large_8n | 14 min | may timeout at 2h |
| 640642 | adios_small_16n | 14 min | |
| 640644 | adios_medium_16n | 14 min | |
| 640646 | adios_large_16n | 14 min | may timeout at 2h |
| **SSD/tmpfs w/ scp staging (parallel)** | | | |
| 640650 | ssd_small_8n | 1 min | |
| 640652 | tmpfs_small_8n | 1 min | |
| 640654 | ssd_medium_8n | 1 min | |
| 640656 | tmpfs_medium_8n | 1 min | |
| 640658 | ssd_large_8n | 1 min | |
| 640660 | tmpfs_large_8n | 1 min | |
| 640662 | ssd_small_16n | 0 min | |

## Pending

**Chain A (sequential, after beegfs_large_16n):**
- 639330–639340: dpm_mixed × small/med/large × 8n/16n (6 jobs, ~5h)

**SSD/tmpfs 16n (parallel, waiting for nodes):**
- 640664–640672: tmpfs_small_16n, ssd/tmpfs_medium_16n, ssd/tmpfs_large_16n (5 jobs)

**Montage synth_small (not yet submitted):**
- 8 remaining: beegfs(8n,16n) + ssd(4n,8n,16n) + tmpfs(4n,8n,16n)
- All sequential due to BeeGFS usage. Est. ~6h total.

## Key Findings

| Finding | Data |
|---------|------|
| **ADIOS fair = much slower than unfair** | small_8n: 13:26 (was 0:27 with computation-only, no file write) |
| **ADIOS Stage 3 (BP5 agg) dominates** | 541s aggregation vs 265s streaming for small_8n |
| **SSD+scp staging = 90% overhead** | Prior test: 509s total, 457s scp (vs BeeGFS 158s) |
| **BeeGFS scales poorly at large** | large_8n: 1:25:55 (vs SSD no-staging 25:31) |
| **beegfs_medium 16n > 8n** | 33:57 vs 16:39 — more total data at 16n |
| **Montage synth_small = 30.7 GB intermediate** | 47 min on beegfs/4n |

## Notes

- ADIOS script now set to 4h timeout for future runs. Current large runs still have 2h limit.
- SSD/tmpfs results now include scp staging (node-to-node data movement between stages).
- Old no-staging SSD/tmpfs results and old unfair ADIOS results archived.
- Montage synth_small chosen as primary dataset (3.2 GB raw, ~30 GB intermediate, ~80 GB total I/O).
