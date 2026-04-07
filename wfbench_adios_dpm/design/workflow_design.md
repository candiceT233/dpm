# Synthetic Workflow Design

## Topology: 3-Stage Pipeline

```
[Stage 1: Producers]          [Stage 2: Consumers]      [Stage 3: Aggregator]
  sim_0  \                   /  analysis_0  \
  sim_1   > -- files -->    >   analysis_1   > -- files --> aggregate_0
  sim_2  /    (large)        \  analysis_2  /    (small)
  ...                         ...
  sim_N                       analysis_N
```

- **Stage 1 (sim)**: N parallel simulation tasks, each writes one large output file
- **Stage 2 (analysis)**: N parallel analysis tasks, each reads one sim output, writes smaller result
- **Stage 3 (aggregate)**: 1 task reads all analysis outputs, writes final summary

This topology is representative of many HPC scientific workflows (genomics,
climate tracking, molecular dynamics) and is the canonical producer-consumer pattern
DPM is designed for.

## Data Size Configurations

All sizes scaled to cluster node memory (set MEM_PER_NODE_GB in config.env).

| Config | Per-task output (Stage 1) | Total intermediate | ADIOS behavior target |
|--------|--------------------------|-------------------|----------------------|
| small  | MEM_PER_NODE_GB * 0.05   | fits in RAM        | ADIOS SST succeeds    |
| medium | MEM_PER_NODE_GB * 0.30   | ~borderline        | ADIOS SST degrades    |
| large  | MEM_PER_NODE_GB * 0.80   | exceeds RAM        | ADIOS SST fails (OOM) |

Example with MEM_PER_NODE_GB=384, NODES=4, tasks_per_node=2 (8 tasks total):
- small:  8 tasks × 384*0.05 GB = 8 × 19.2 GB = ~154 GB total
- medium: 8 tasks × 384*0.30 GB = 8 × 115 GB = ~922 GB total
- large:  8 tasks × 384*0.80 GB = 8 × 307 GB = ~2.4 TB total

Note: Adjust TASKS_PER_NODE to keep experiment tractable. Start with smaller
fractions if cluster resources are limited.

## I/O Patterns (per task)

### Stage 1 (sim): Sequential write
- Operation type: sequential write (sw)
- Transfer size: 1MB (typical simulation checkpoint pattern)
- Output: one HDF5/binary file per task
- I/O intensity: ~95% of task runtime is I/O

### Stage 2 (analysis): Random read + sequential write
- Operation type: random read (rr), then sequential write (sw)
- Transfer size for read: 4KB–64KB (typical feature extraction pattern)
- Output: reduced result file (1/8th the size of input)
- I/O intensity: ~70% of task runtime is I/O

### Stage 3 (aggregate): Sequential read + sequential write
- Operation type: sequential read (sr), sequential write (sw)
- Transfer size: 1MB
- Output: summary file (~100MB)
- I/O intensity: ~80% of task runtime is I/O

## Why This Design Stresses ADIOS SST

ADIOS SST (Sustainable Staging Transport) requires:
1. Producer and consumer to be running **simultaneously** — they handshake via a
   rendezvous server. In HPC batch scheduling, Stage 1 often completes before
   Stage 2 starts, breaking the SST connection.
2. Data to fit in **memory buffers** — SST transfers data through RDMA/network memory.
   When Stage 1 output exceeds available memory, SST either blocks indefinitely or OOMs.

**Failure mode 1 — time decoupling** (always present in batch scheduling):
- Slurm job for Stage 1 finishes → SST rendezvous server closes
- Stage 2 job starts → cannot connect to Stage 1 → timeout / error

**Failure mode 2 — memory overflow** (large config):
- Each sim task tries to push 307GB through SST memory buffer
- Node has 384GB total RAM (shared with OS, MPI buffers, etc.)
- OOM kill or SST stall

## How DPM Is Evaluated

DPM does not run live during these experiments. Instead, DPM scores are computed
**offline** from IOR profiling data already collected on the target cluster, then
compared against the actual measured workflow times.

### DPM Score Definition

For each producer-consumer pair and each storage tier, DPM computes:

```
DPM_score = estT_prod + estT_cons
```

Where `estT_prod` and `estT_cons` are the estimated I/O times for the producer
(write) and consumer (read) operations, predicted by the linear regression model
trained on IOR profiling data. **Lower DPM score = better predicted performance.**

### Evaluation Logic

1. Run all storage tiers (tmpfs, ssd, beegfs) on all data sizes → record `total_time_s`
2. Compute DPM score for each (tier, data size, I/O pattern) using profiling data
3. Rank tiers by DPM score (ascending) and by actual time (ascending)
4. **Key claim**: DPM rank matches actual rank — the tier DPM scores lowest is the
   tier that actually ran fastest

### Target Result Table

| Size   | Tier   | DPM Score | DPM Rank | Actual Time | Actual Rank | Match? |
|--------|--------|-----------|----------|-------------|-------------|--------|
| small  | tmpfs  | lowest    | 1        | fastest     | 1           | YES    |
| small  | ssd    | mid       | 2        | mid         | 2           | YES    |
| small  | beegfs | highest   | 3        | slowest     | 3           | YES    |
| medium | ssd    | lowest    | 1        | fastest     | 1           | YES    |
| medium | beegfs | mid       | 2        | mid         | 2           | YES    |
| medium | tmpfs  | highest   | 3        | slowest/OOM | 3           | YES    |
| large  | ssd    | lowest    | 1        | fastest     | 1           | YES    |
| large  | beegfs | mid       | 2        | mid         | 2           | YES    |
| large  | tmpfs  | —         | N/A      | OOM/FAIL    | N/A         | —      |

And separately, ADIOS SST fails on large data — showing DPM's file-based storage
selection is necessary even before ranking matters.

### What This Demonstrates

- DPM correctly identifies the best storage tier without exhaustive trial
- The "trick": by showing DPM score rank = actual time rank across all configurations,
  we validate that DPM's prediction model generalizes to this new synthetic workload
- ADIOS SST failure establishes the motivation: in-situ streaming is not always viable,
  and DPM's storage selection fills that gap
