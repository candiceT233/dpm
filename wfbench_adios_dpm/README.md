# WfBench + ADIOS vs DPM Evaluation

## Purpose

This experiment supports the SC26 DPM paper revision by demonstrating scenarios where
ADIOS in-memory streaming (SST engine) fails or degrades, while DPM's storage-aware
scheduling succeeds. It directly addresses Reviewer B's suggestion to compare against
in-situ/streaming baselines using WfBench synthetic workflows.

## Core Argument

ADIOS SST (Sustainable Staging Transport) bypasses shared storage by coupling producer
and consumer tasks through in-memory buffers. This works well when:
- Data volume fits within available node memory
- Producer and consumer can be co-scheduled simultaneously

DPM targets the complementary regime where storage-based communication is necessary:
- Intermediate data exceeds per-node memory capacity
- Producer and consumer run as separate batch jobs (time-decoupled)
- Tasks are heterogeneous and cannot be co-located

**Expected result**: ADIOS SST fails (OOM or connection timeout) on large-data
configurations; DPM selects the correct storage tier and completes successfully.

## Folder Structure

```
wfbench_adios_dpm/
├── README.md                    # This file
├── PLAN.md                      # Step-by-step experimental plan
├── design/
│   ├── workflow_design.md       # Synthetic workflow specification
│   ├── experiment_matrix.md     # All configurations to test
│   └── failure_analysis.md      # Detailed ADIOS failure scenarios
├── wfbench/
│   ├── generate_workflow.py     # Generates WfBench JSON workflow
│   ├── workflow_small.json      # Small data: ~4GB intermediate (ADIOS works)
│   ├── workflow_medium.json     # Medium data: ~40GB intermediate (ADIOS marginal)
│   └── workflow_large.json      # Large data: ~200GB intermediate (ADIOS fails)
├── adios/
│   ├── adios2.xml               # ADIOS2 engine config (SST + BP5)
│   ├── producer_task.py         # ADIOS-coupled producer task
│   └── consumer_task.py         # ADIOS-coupled consumer task
├── scripts/
│   ├── setup_env.sh             # Environment setup (modules, conda, pip)
│   ├── run_storage.sh           # Run workflow with file-based storage (DPM config)
│   ├── run_adios_sst.sh         # Run workflow with ADIOS SST engine
│   └── collect_results.sh       # Gather timing and error results
└── analysis/
    └── compare_results.py       # Compare ADIOS vs DPM outcomes
```

## Quick Start (on PNNL cluster)

```bash
# 1. Clone and enter directory
cd wfbench_adios_dpm/

# 2. Set up environment
bash scripts/setup_env.sh

# 3. Generate synthetic workflows
cd wfbench/
python generate_workflow.py --size small   # ~4GB
python generate_workflow.py --size medium  # ~40GB
python generate_workflow.py --size large   # ~200GB

# 4. Run ADIOS SST baseline (will fail on large)
bash scripts/run_adios_sst.sh large

# 5. Run DPM storage config (should succeed on all)
bash scripts/run_storage.sh large --storage ssd
bash scripts/run_storage.sh large --storage beegfs

# 6. Collect and compare results
bash scripts/collect_results.sh
python analysis/compare_results.py
```

## Dependencies

- Python >= 3.11
- wfcommons >= 1.4 (`pip install wfcommons`)
- ADIOS2 >= 2.9 (with SST and BP5 engines)
- MPI (OpenMPI or MPICH)
- Access to cluster storage: local SSD, TMPFS (node-local), BeeGFS (shared)

## TODO: Fill in before running

See `PLAN.md` Step 0 for the system-specific variables to set:
- Cluster partition name and node configuration
- Path to local SSD mount point per node
- Path to BeeGFS mount point
- ADIOS2 module name on cluster
- Available memory per node (to set data size thresholds correctly)
