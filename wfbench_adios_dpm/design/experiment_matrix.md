# Experiment Matrix

## Evaluation Goal

Demonstrate that DPM's score (lower = better) correctly ranks storage tiers
by actual performance. All storage tiers are run on all data sizes so the
predicted ranking can be validated against measured timing.

ADIOS SST is run only on the large-data case to show the failure mode that
motivates file-based storage selection — it is not part of the DPM ranking
comparison.

## Fixed Variables

| Variable        | Value                         | Notes |
|-----------------|-------------------------------|-------|
| Partition       | slurm                         | dc-class nodes (dcXXX) |
| Node pattern    | dcXXX                         | homogeneous hardware |
| Tasks per node  | CORES_PER_NODE / 2            | set after probe job |
| Runs per config | 3                             | for mean ± std dev |

## Phase 1+2: DPM Score Ranking Validation (4 nodes)

Run all storage tiers at all data sizes. Compare DPM score rank vs actual time rank.

| Run ID | Size   | Backend    | Nodes | Expected DPM Rank | Expected Outcome   | Priority |
|--------|--------|------------|-------|-------------------|--------------------|----------|
| 01     | small  | tmpfs      | 4     | 1 (best)          | SUCCESS, fastest   | High     |
| 02     | small  | ssd        | 4     | 2                 | SUCCESS            | High     |
| 03     | small  | beegfs     | 4     | 3                 | SUCCESS, slowest   | High     |
| 04     | medium | ssd        | 4     | 1 (best)          | SUCCESS, fastest   | High     |
| 05     | medium | beegfs     | 4     | 2                 | SUCCESS            | High     |
| 06     | medium | tmpfs      | 4     | 3                 | FAIL (no space)    | High     |
| 07     | large  | ssd        | 4     | 1 (best)          | SUCCESS, fastest   | High     |
| 08     | large  | beegfs     | 4     | 2                 | SUCCESS            | High     |
| 09     | large  | tmpfs      | 4     | N/A               | FAIL (no space)    | Low      |
| 10     | large  | adios_sst  | 4     | N/A (not ranked)  | FAIL (OOM/timeout) | High     |

> Note: Expected DPM ranks are predictions based on I/O pattern characteristics.
> Actual DPM scores are computed offline from cluster IOR profiling data after
> the probe job confirms storage availability.

Subtotal: 10 configs × 3 runs = **30 jobs**

## Phase 3: Node-Count Scaling (large data, top DPM-ranked tier)

Use the storage tier DPM ranked #1 for large data and scale nodes.
Confirms DPM selection holds at scale; ADIOS SST excluded (already fails at 4 nodes).

| Run ID | Size  | Backend         | Nodes | Expected Outcome | Priority |
|--------|-------|-----------------|-------|------------------|----------|
| 11     | large | DPM top choice  | 8     | SUCCESS          | High     |
| 12     | large | DPM top choice  | 16    | SUCCESS          | High     |
| 13     | large | DPM top choice  | 32    | SUCCESS          | High     |

Subtotal: 3 configs × 3 runs = **9 jobs**

## Total

| Phase     | Jobs | Description |
|-----------|------|-------------|
| Phase 1+2 | 30   | DPM ranking validation across all tiers and data sizes |
| Phase 3   | 9    | Node-count scaling with DPM top-ranked tier |
| **Total** | **39** | |

## DPM Score Computation (offline, after runs complete)

After all timing results are collected, compute DPM scores using IOR profiling
data from the cluster:

```bash
python analysis/dpm_score_comparison.py \
    --results   results/all_results.csv \
    --profiles  ${DPM_PROFILE_DIR} \
    --workflow  wfbench/workflow_large.json \
    --output    results/
```

This produces:
- `results/dpm_score_ranking.csv` — DPM score and actual time per (size, tier), ranked
- `results/ranking_comparison.pdf` — side-by-side bar chart of DPM rank vs actual rank

## Minimum Viable Result for Paper

| Priority | Runs | What it shows |
|----------|------|---------------|
| Must have | 01,02,03,04,05,07,08,10 | DPM ranking correct for small+medium+large; ADIOS SST fails |
| Should have | 06,09 | Confirms tmpfs OOM on medium/large |
| Nice to have | 11,12,13 | Scalability to 32 nodes |

Minimum: 8 configs × 3 runs = **24 jobs**
