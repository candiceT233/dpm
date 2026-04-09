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

## ADIOS SST — previous results INVALIDATED

- v1 (639366–639376): had numpy computation, no Stage 3, 2x task allocation
- v2 (640636–640646): no computation but wrote ALL data (8x more I/O than file-based)
- All archived. See FAIRNESS_FIX_NOTES.md for details.

## ADIOS SST v3 (fair: 1/8 reduction, BP5 output, 4h limit)

| Job ID | Config | Stage 1+2 | Stage 3 | Total | Status |
|--------|--------|-----------|---------|-------|--------|
| 640699 | adios_small_8n | 197s | 46s | **243s (4:03)** | SUCCESS |
| 640701 | adios_medium_8n | 1591s | 281s | **1872s (31:12)** | SUCCESS |
| 640703 | adios_large_8n | | | running (34 min) | |
| 640705 | adios_small_16n | 194s | 85s | **279s (4:39)** | FAILED (2/32) |
| 640707 | adios_medium_16n | 1621s | 569s | **2190s (36:30)** | SUCCESS |
| 640709 | adios_large_16n | running |

## Completed — WfBench tmpfs w/ scp staging

| Job ID | Config | Stage1 | scp 1→2 | Stage2 | scp 2→3 | Total | Status |
|--------|--------|--------|---------|--------|---------|-------|--------|
| 640652 | tmpfs_small_8n | 9s | 258s | 11s | 222s | **515s** | SUCCESS (scp=93%) |
| 640656 | tmpfs_medium_8n | 46s | 10s | 0s | 17s | 73s | **FAILED** (24/32 — tmpfs OOM) |
| 640660 | tmpfs_large_8n | 53s | 9s | 1s | 14s | 77s | **FAILED** (32/32 — tmpfs OOM) |
| 640664 | tmpfs_small_16n | — | 254s | — | 374s | **715s** | SUCCESS (scp=88%) |
| 640668 | tmpfs_medium_16n | — | 9s | — | 24s | 84s | **FAILED** (48/64 — tmpfs OOM) |
| 640672 | tmpfs_large_16n | — | 9s | — | 26s | 89s | **FAILED** (64/64 — tmpfs OOM) |

## Completed — WfBench SSD w/ scp staging

| Job ID | Config | Stage1 | scp 1→2 | Stage2 | scp 2→3 | Total | Status |
|--------|--------|--------|---------|--------|---------|-------|--------|
| 640650 | ssd_small_8n | 27s | 295s | 3s | 222s | **585s** | SUCCESS (scp=88%) |
| 640654 | ssd_medium_8n | 370s | 1447s | 24s | 1047s | **2933s** | FAILED (3/16, scp=85%) |
| 640658 | ssd_large_8n | — | — | — | — | 1:04:50 | **FAILED** (SSD full) |
| 640666 | ssd_medium_16n | 774s | 1532s | 25s | 1259s | **3590s** | FAILED (3/16, scp=78%) |
| 640662 | ssd_small_16n | — | 250s | — | 379s | **716s** | SUCCESS (scp=88%) |
| 640670 | ssd_large_16n | — | — | — | — | 35:53 | **FAILED** (SSD full — 400GB > 477GB) |

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
