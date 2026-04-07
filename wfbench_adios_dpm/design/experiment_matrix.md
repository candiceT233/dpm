# Experiment Matrix

## Variables

| Variable          | Values                          | Notes |
|-------------------|---------------------------------|-------|
| Data size         | small, medium, large            | See workflow_design.md |
| Backend           | adios_sst, ssd, beegfs, tmpfs   | adios_sst = ADIOS2 SST engine |
| Nodes             | 4                               | Fixed for paper |
| Tasks per stage   | 8 (2 per node)                  | Adjust per cluster |
| Runs per config   | 3                               | For mean and std dev |

## Full Test Matrix

| Run ID | Size   | Backend    | Expected Outcome       | Priority |
|--------|--------|------------|------------------------|----------|
| 01     | small  | adios_sst  | SUCCESS, ~X sec        | High     |
| 02     | small  | tmpfs      | SUCCESS, ~X sec        | High     |
| 03     | small  | ssd        | SUCCESS, ~X sec        | High     |
| 04     | small  | beegfs     | SUCCESS, ~X sec        | Medium   |
| 05     | medium | adios_sst  | DEGRADED or FAIL       | High     |
| 06     | medium | ssd        | SUCCESS, ~X sec        | High     |
| 07     | medium | beegfs     | SUCCESS, ~X sec        | High     |
| 08     | medium | tmpfs      | FAIL (no space) or OK  | Medium   |
| 09     | large  | adios_sst  | FAIL (OOM / timeout)   | High     |
| 10     | large  | ssd        | SUCCESS, ~X sec        | High     |
| 11     | large  | beegfs     | SUCCESS, ~X sec        | High     |
| 12     | large  | tmpfs      | FAIL (no space)        | Low      |

Total: 12 configurations × 3 runs = 36 jobs

## Metrics to Record per Run

For each job, record:
- Wall time (total, stage 1, stage 2, stage 3)
- I/O time (from Darshan or manual timing)
- Peak memory usage (from /proc or SLURM accounting)
- Exit status (SUCCESS / OOM / TIMEOUT / OTHER_ERROR)
- Error message (if failed)
- Storage throughput observed (MB/s)

## Minimum Viable Result for Paper

If cluster time is limited, prioritize runs marked "High" above (8 configs × 3 runs = 24 jobs).

The essential contrast for the paper is:
- Run 09 (large + adios_sst) = FAIL
- Run 10 or 11 (large + ssd/beegfs) = SUCCESS

This directly supports the paper's argument that storage-based scheduling is necessary
when in-situ streaming is infeasible.
