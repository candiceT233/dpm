# WfBench ADIOS vs DPM: Experiment Goal

## Motivation

Reviewer B (HPDC submission) identified a critical gap: the paper omits comparison with in-situ and streaming workflow systems such as ADIOS, LowFive, and RADICAL-based frameworks. These systems address producer-consumer data exchange through fundamentally different mechanisms — in-memory coupling rather than shared storage — and their absence challenges DPM's core assumption that storage selection is the primary optimization lever for workflow I/O.

Luke (IIT co-author) directly recommended: "Have evaluation comparing against existing streaming systems (like ADIOS) with WfBench," specifically to demonstrate cases where shared storage has benefit over streaming engines, such as when intermediate data exceeds available memory.

## What This Experiment Demonstrates

This experiment answers two questions:

### Q1: Does DPM correctly rank storage tiers for a new (synthetic) workflow?

**Why it matters:** The current paper evaluates DPM on three real workflows (1000 Genomes, PyflexTRKR, DeepDriveMD) but reviewers questioned whether accuracy generalizes beyond these. By running a WfBench-generated synthetic workflow with known I/O characteristics across all available storage tiers (tmpfs, SSD, BeeGFS), we validate that DPM's IOR-trained surrogate model predicts the correct performance ranking without exhaustive trial runs.

**Method:**
- Generate a 3-stage producer-consumer workflow at three data sizes (small, medium, large) using WfBench
- Run each size on all storage tiers (tmpfs, SSD, BeeGFS) on 4 nodes × 3 repetitions
- Compute DPM scores offline from existing IOR profiling data
- Compare DPM's predicted tier ranking against measured runtime ranking

**Success criterion:** DPM rank matches actual performance rank for each data size.

### Q2: When does in-situ streaming (ADIOS SST) fail, and does DPM cover that regime?

**Why it matters:** In-situ coupling (ADIOS SST) is the strongest alternative to file-based producer-consumer communication. If ADIOS SST always worked, DPM's storage-selection approach would be unnecessary. This experiment identifies the regime boundary where in-situ streaming breaks down and DPM's file-based approach becomes essential.

**Method:**
- Run the same synthetic workflow with ADIOS2 SST engine at each data size
- SST couples producers and consumers through in-memory RDMA/TCP buffers — data never touches disk

**Expected failure modes:**
1. **Memory overflow:** When per-task intermediate data exceeds ~60% of node RAM (~230 GB on 384 GB nodes), SST buffers overflow → OOM kill or write() blocks indefinitely
2. **Time decoupling:** Under standard batch scheduling, producer and consumer run as separate Slurm jobs. SST requires simultaneous execution; the rendezvous server closes when the producer job exits, so the consumer job cannot connect

**Success criterion:** ADIOS SST succeeds on small data but fails on large data (OOM or timeout), while DPM-selected storage (SSD or BeeGFS) completes successfully at all sizes.

## How Results Map to Paper Claims

| Paper Claim | Evidence from This Experiment |
|---|---|
| DPM generalizes to new workflows | DPM rank matches actual rank on a 4th (synthetic) workflow |
| In-situ streaming is complementary, not a replacement | ADIOS SST fails when data > node memory or jobs are time-decoupled |
| File-based storage is the right abstraction for production HPC workflows | DPM completes at all data sizes; ADIOS SST does not |
| DPM selects optimal storage without exhaustive search | DPM score ranking validated against measured runtimes |

## Experiment Scope

- **Configurations:** 10 (size × tier) combinations + 3 node-scaling runs = 39 total jobs (13 configs × 3 reps)
- **Minimum viable:** 8 configs × 3 reps = 24 jobs (covers ranking validation + ADIOS failure)
- **Cluster:** 4-node baseline on dc-class nodes (dual AMD EPYC 7502, 384 GB RAM, local SSD, BeeGFS)
- **Node scaling (Phase 3):** 8, 16, 32 nodes on DPM's top-ranked tier for large data

## Paper Placement

Results go in **Section 5.5: "Comparison with In-Situ Streaming (ADIOS)"** with:
- A bar chart showing wall time for ADIOS SST vs DPM-selected storage across data sizes (ADIOS bar marked "FAILED" for large)
- A table showing DPM predicted rank vs actual measured rank per (size, tier)
- 1–2 paragraphs connecting results back to the Related Work positioning: DPM targets the majority of production HPC workflows that rely on storage-based communication because they are time-decoupled, require persistent intermediate data, or exceed per-node memory capacity
