# Experimental Plan: WfBench ADIOS vs DPM

## Goal

Produce a figure and table for the SC26 paper showing:
1. ADIOS SST fails (OOM or timeout) when intermediate data exceeds per-node memory
2. DPM selects correct storage tier and completes successfully in both cases
3. DPM runtime on best storage is competitive with ADIOS on small data

## Step 0: System Configuration (fill in before running)

Create a file `config.env` in this directory with your cluster settings:

```bash
# config.env — fill in for your PNNL cluster
CLUSTER_NAME="TODO"            # e.g., deception, tahoma, constance
PARTITION="TODO"               # SLURM partition for compute nodes
NODES=4                        # Number of nodes for experiment
CORES_PER_NODE=TODO            # Physical cores per node
MEM_PER_NODE_GB=TODO           # Total RAM per node in GB (e.g., 384)
LOCAL_SSD_PATH="TODO"          # e.g., /local/scratch or /nvme
BEEGFS_PATH="TODO"             # e.g., /rcfs/projects/...
TMPFS_PATH="/dev/shm"          # Usually /dev/shm
ADIOS2_MODULE="TODO"           # e.g., adios2/2.9.1
PYTHON_ENV="TODO"              # Conda env or virtualenv path
```

## Step 1: Environment Setup

```bash
source config.env
bash scripts/setup_env.sh
```

Installs: `wfcommons`, `adios2` Python bindings, `mpi4py`, numpy, pandas.

## Step 2: Determine Data Size Thresholds

Based on `MEM_PER_NODE_GB`, set three workflow sizes:

| Size   | Intermediate data per node | Expected ADIOS behavior |
|--------|---------------------------|------------------------|
| small  | ~10% of node RAM          | ADIOS SST: OK          |
| medium | ~60% of node RAM          | ADIOS SST: marginal    |
| large  | ~150% of node RAM         | ADIOS SST: OOM / fail  |

Example for 384GB node:
- small:  ~40GB total / 4 nodes = ~10GB/node intermediate data
- medium: ~240GB total / 4 nodes = ~60GB/node
- large:  ~600GB total / 4 nodes = ~150GB/node (exceeds RAM)

Update `wfbench/generate_workflow.py` with the actual thresholds for your system.

## Step 3: Generate Synthetic Workflows

```bash
cd wfbench/
python generate_workflow.py --size small   --nodes ${NODES} --output workflow_small.json
python generate_workflow.py --size medium  --nodes ${NODES} --output workflow_medium.json
python generate_workflow.py --size large   --nodes ${NODES} --output workflow_large.json
```

This produces WfFormat JSON files defining the 3-stage producer-consumer workflow
(see `design/workflow_design.md` for the topology).

## Step 4: Run DPM Storage Profiling (one-time)

If IOR profiles for the cluster storage are not yet collected, run:

```bash
# TODO: link to DPM profiling scripts in perf_profiles/
# bash ../perf_profiles/run_ior_profile.sh --storage ssd
# bash ../perf_profiles/run_ior_profile.sh --storage beegfs
# bash ../perf_profiles/run_ior_profile.sh --storage tmpfs
```

If profiles already exist for this cluster, skip this step.

## Step 5: Run DPM Storage Selection

Run DPM's performance matching on the workflow profiles to get the recommended
storage-parallelism for each size:

```bash
# TODO: run DPM matching script on each workflow JSON
# python ../workflow_analysis/run_dpm.py --workflow wfbench/workflow_large.json
```

Record DPM's recommendation (expected: SSD or BeeGFS for large data).

## Step 6: Run ADIOS SST Baseline

```bash
# Small (should succeed)
bash scripts/run_adios_sst.sh --size small  --nodes ${NODES}

# Medium (may degrade or OOM)
bash scripts/run_adios_sst.sh --size medium --nodes ${NODES}

# Large (expected to fail with OOM or SST connection timeout)
bash scripts/run_adios_sst.sh --size large  --nodes ${NODES}
```

Record: success/failure, wall time, peak memory usage, error messages.

## Step 7: Run File-Based Storage (DPM Configuration)

Run each size on the storage DPM recommends, plus all alternatives for comparison:

```bash
for STORAGE in ssd beegfs tmpfs; do
  for SIZE in small medium large; do
    bash scripts/run_storage.sh --size ${SIZE} --storage ${STORAGE} --nodes ${NODES}
  done
done
```

Record: wall time, I/O time, data movement time.

## Step 8: Collect and Analyze Results

```bash
bash scripts/collect_results.sh --output results/

python analysis/compare_results.py \
    --results results/ \
    --output results/comparison_table.csv
```

## Step 9: Produce Paper Figures

The analysis script generates:
1. **Bar chart**: Wall time for ADIOS SST vs DPM-selected storage across three data sizes
   - ADIOS SST bar = "FAILED" for large data (shown as error bar or hatched)
   - DPM bar = measured runtime
2. **Table**: Success/failure + runtime for each combination

## Expected Results

| Data Size | ADIOS SST       | DPM (SSD)  | DPM (BeeGFS) |
|-----------|----------------|------------|--------------|
| Small     | ~X sec (OK)     | ~X sec     | ~X sec       |
| Medium    | ~X sec (OK/OOM) | ~X sec     | ~X sec       |
| Large     | FAILED (OOM)    | ~X sec     | ~X sec       |

## Paper Section Placement

Results go in Section 5 (Evaluation) as a new subsection:
"5.5 Comparison with In-Situ Streaming (ADIOS)"

Key message: DPM covers the regime where in-situ streaming is not applicable —
when intermediate data exceeds memory or tasks cannot be co-scheduled.
