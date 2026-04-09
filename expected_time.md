# DPM Evaluation — Job Completion Tracker

**Updated:** 2026-04-08 16:15 PDT
**Goal:** Collect all results needed to start writing the paper.

## What's needed to start writing

| Experiment | Configs | Status | ETA |
|-----------|---------|--------|-----|
| WfBench SSD (8n, 16n) × small/med/large | 6 | **DONE** | — |
| WfBench tmpfs (8n, 16n) × small/med/large | 6 | **DONE** | — |
| WfBench BeeGFS (8n, 16n) × small/med/large | 6 | 2 done, 1 running, 3 pending | ~3h |
| WfBench DPM mixed (8n, 16n) × small/med/large | 6 | 0 done, 6 pending | ~5h after BeeGFS |
| ADIOS SST (8n, 16n) × small/med/large | 6 | 4 done, 2 running | ~30 min |
| Montage synth_medium × beegfs/ssd/tmpfs × 4/8/16n | 9 | 0 done, 1 testing | ~6h after test |
| **Total** | **39** | **18 done** | |

**Earliest paper-writing start:** ~Apr 9, 2026 04:00 AM PDT (all WfBench + ADIOS done, Montage mostly done)

## Completed Results

### WfBench SSD (Chain B — done)

| Job ID | Config | Elapsed |
|--------|--------|---------|
| 639342 | ssd_small_8n | 2:54 |
| 639344 | ssd_medium_8n | 18:33 |
| 639346 | ssd_large_8n | 25:31 |
| 639348 | ssd_small_16n | 5:24 |
| 639350 | ssd_medium_16n | 42:12 |
| 639352 | ssd_large_16n | 27:21 |

### WfBench tmpfs (Chain B — done)

| Job ID | Config | Elapsed |
|--------|--------|---------|
| 639354 | tmpfs_small_8n | 2:20 |
| 639356 | tmpfs_medium_8n | 2:14 |
| 639358 | tmpfs_large_8n | 2:33 |
| 639360 | tmpfs_small_16n | 4:11 |
| 639362 | tmpfs_medium_16n | 2:46 |
| 639364 | tmpfs_large_16n | 3:13 |

### ADIOS SST (Chain B — ALL DONE)

| Job ID | Config | Elapsed | Status |
|--------|--------|---------|--------|
| 639366 | adios_small_8n | 0:27 | SUCCESS |
| 639368 | adios_medium_8n | 3:15 | SUCCESS |
| 639370 | adios_large_8n | 2:00:00 | **TIMEOUT** (hit 2h limit) |
| 639372 | adios_small_16n | 0:31 | SUCCESS |
| 639374 | adios_medium_16n | 3:46 | SUCCESS |
| 639376 | adios_large_16n | 2:00:09 | **TIMEOUT** (hit 2h limit) |

### WfBench BeeGFS (Chain A — 2/6 done)

| Job ID | Config | Elapsed |
|--------|--------|---------|
| 639318 | beegfs_small_8n | 2:38 |
| 639320 | beegfs_medium_8n | 16:39 |
| 639322 | beegfs_large_8n | 1:25:55 |
| 639324 | beegfs_small_16n | 5:03 |

### Montage (real 2MASS small, beegfs only — done)

| Job ID | Config | Elapsed |
|--------|--------|---------|
| 639126 | beegfs_small_4n | 3:35 |
| 639291 | beegfs_small_8n | 2:13 |
| 639297 | beegfs_small_16n | 1:30 |

## Currently Running

| Job ID | Config | Elapsed | Est. remaining |
|--------|--------|---------|---------------|
| 639326 | wf_beegfs_medium_16n | 1:26 | ~28 min |
| 639696 | montage_synth_small_beegfs_4n (test) | 39 min | ~20 min |
| 640605 | wf_ssd_small_8n (scp staging test) | just started | ~5 min |

## Pending — Chain A (sequential, BeeGFS)

| Job ID | Config | Est. Time |
|--------|--------|-----------|
| 639324 | beegfs_small_16n | ~6 min |
| 639326 | beegfs_medium_16n | ~30 min |
| 639328 | beegfs_large_16n | ~120 min |
| 639330 | dpm_mixed_small_8n | ~4 min |
| 639332 | dpm_mixed_medium_8n | ~20 min |
| 639334 | dpm_mixed_large_8n | ~60 min |
| 639336 | dpm_mixed_small_16n | ~6 min |
| 639338 | dpm_mixed_medium_16n | ~40 min |
| 639340 | dpm_mixed_large_16n | ~120 min |
| **Total** | **9 jobs** | **~406 min (~6.8h)** |

## Pending — Montage synth_medium (not yet submitted)

Waiting for test job 639686 to validate pipeline, then submit 9 jobs:
- synth_medium × beegfs/ssd/tmpfs × 4/8/16 nodes (all sequential, ~6h total)
- Note: Montage SSD/tmpfs staging scripts have been fixed (use script files)

## Key Findings (paper-ready)

| Finding | Data |
|---------|------|
| **tmpfs >> SSD >> BeeGFS** for WfBench | tmpfs: 2-4 min, SSD: 3-42 min, BeeGFS: 3-17+ min (large still running) |
| **16n slower than 8n for SSD medium** | 42 min vs 18 min — 2.4 TB total data overwhelms per-node SSD bandwidth |
| **ADIOS SST succeeds at medium scale** | small+medium SUCCESS on 8n/16n with co-launch fix |
| **ADIOS SST rendezvous fails with separate srun** | 8n: 16/16 failed, 16n: 32/32 failed (old approach) |
| **Montage scales with nodes (real data)** | 4n: 3:35, 8n: 2:13, 16n: 1:30 |
| **Synthetic FITS valid for Montage** | mImgtbl parses all, mProject produces correct output |
| **~2.6× I/O amplification in Montage** | Read amplification from fan-out DAG structure |

## Third node scale decision

After 8n/16n results are complete:
- If 16n is consistently slower → use **4/8/16** (show diminishing returns)
- If 16n still scales → use **8/16/32** (push further)
- Current evidence: 16n slower for WfBench SSD medium, faster for Montage → likely **4/8/16**
