# Experiment Matrix

## Fixed Variables

| Variable        | Value                         | Notes |
|-----------------|-------------------------------|-------|
| Partition       | slurm                         | dc-class nodes (dcXXX) |
| Node pattern    | dcXXX                         | e.g. dc001, dc128 — homogeneous hardware |
| Tasks per node  | CORES_PER_NODE / 2            | Set after probe job; leave one core for OS |
| Runs per config | 3                             | For mean ± std dev |

## Phase 1+2: Data-Size Sweep (4 nodes fixed)

Goal: show ADIOS SST fails on large data while DPM succeeds on all sizes.

| Run ID | Size   | Backend    | Nodes | Expected Outcome         | Priority |
|--------|--------|------------|-------|--------------------------|----------|
| 01     | small  | adios_sst  | 4     | SUCCESS                  | High     |
| 02     | small  | tmpfs      | 4     | SUCCESS (fastest)        | High     |
| 03     | small  | ssd        | 4     | SUCCESS                  | High     |
| 04     | small  | beegfs     | 4     | SUCCESS                  | Medium   |
| 05     | medium | adios_sst  | 4     | DEGRADED or FAIL         | High     |
| 06     | medium | ssd        | 4     | SUCCESS                  | High     |
| 07     | medium | beegfs     | 4     | SUCCESS                  | High     |
| 08     | medium | tmpfs      | 4     | FAIL (no space) or OK    | Medium   |
| 09     | large  | adios_sst  | 4     | **FAIL** (OOM / timeout) | High     |
| 10     | large  | ssd        | 4     | SUCCESS                  | High     |
| 11     | large  | beegfs     | 4     | SUCCESS                  | High     |
| 12     | large  | tmpfs      | 4     | FAIL (no space)          | Low      |

Subtotal: 12 configs × 3 runs = **36 jobs**

## Phase 3: Node-Count Scaling (large data, DPM storage only)

Goal: show DPM storage selection remains effective at scale (up to 32 nodes).
ADIOS SST is excluded — it already fails at 4 nodes.

| Run ID | Size  | Backend | Nodes | Expected Outcome | Priority |
|--------|-------|---------|-------|------------------|----------|
| 13     | large | ssd     | 8     | SUCCESS          | High     |
| 14     | large | beegfs  | 8     | SUCCESS          | High     |
| 15     | large | ssd     | 16    | SUCCESS          | High     |
| 16     | large | beegfs  | 16    | SUCCESS          | High     |
| 17     | large | ssd     | 32    | SUCCESS          | High     |
| 18     | large | beegfs  | 32    | SUCCESS          | High     |

Subtotal: 6 configs × 3 runs = **18 jobs**

## Total

| Phase   | Jobs | Description |
|---------|------|-------------|
| Phase 1+2 | 36 | Data-size sweep at 4 nodes |
| Phase 3   | 18 | Node-count scaling to 32 nodes |
| **Total** | **54** | |

## Metrics to Record per Run

- Wall time: total, stage 1, stage 2, stage 3
- Exit status: SUCCESS / OOM / TIMEOUT / OTHER_ERROR
- Error message if failed
- Node count and storage backend

## Minimum Viable Result for Paper

If cluster time is limited, the essential result set is:

1. **Run 09** (large + adios_sst + 4 nodes) = FAIL — proves ADIOS SST cannot handle this regime
2. **Runs 10–11** (large + ssd/beegfs + 4 nodes) = SUCCESS — proves DPM storage selection works
3. **Runs 13–18** (large + ssd/beegfs + 8/16/32 nodes) = SUCCESS — proves scalability

This is 9 configs × 3 runs = **27 jobs** minimum.
