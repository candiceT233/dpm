# SETUP_AGENT.md — Onboarding Guide for New Cluster Environment

This file is written for an AI agent or human who is setting up this evaluation from scratch
on a new HPC cluster. It covers: discovering the cluster environment, filling in config,
setting up software dependencies, and submitting Slurm jobs.

---

## Step 0: Discover Cluster Environment

Run the following commands to collect the information needed to fill in `config.env`.

### Identify yourself and your allocations

```bash
# Who are you and what accounts are available
whoami
groups
sacctmgr show user $(whoami) withassoc format=user,account,partition -p 2>/dev/null || \
  sshare -u $(whoami) 2>/dev/null || \
  echo "Try: squeue --me or check with cluster admin"
```

### Find partitions and node names

```bash
# List available partitions and node counts
sinfo -o "%P %a %l %D %C" 2>/dev/null | head -30

# List actual node names in each partition (you need a specific node name for the probe job below)
sinfo -p PARTITION_NAME -o "%N %m %c %G" | head -20

# Get node names only (pick one to use in the probe job)
sinfo -p PARTITION_NAME -o "%N" | head -10
```

> **WARNING**: `scontrol show node` on the head/login node reports login node specs,
> not compute node specs. RAM, CPU count, and storage mounts on compute nodes may differ.
> Always use the probe job below to get accurate compute node specs.

### Probe a compute node for actual specs (required)

Submit a short job to get real compute node hardware info. Replace `PARTITION_NAME`,
`ACCOUNT_NAME`, and optionally `NODE_NAME` (from `sinfo` above) with actual values:

```bash
sbatch --partition=PARTITION_NAME \
       --account=ACCOUNT_NAME \
       --nodes=1 --ntasks=1 --time=00:05:00 \
       --nodelist=NODE_NAME \
       --output=/tmp/node_probe_%j.out \
       --wrap="
echo '=== Node: ' \$(hostname)
echo '=== CPUs:' \$(nproc)
echo '=== RAM:'
free -h
echo '=== Storage mounts:'
df -hT | grep -v tmpfs | grep -v overlay
echo '=== Local scratch (check common paths):'
ls /local/ /local/scratch/ /nvme/ /scratch/ 2>/dev/null || echo 'none found'
echo '=== TMPFS (/dev/shm):'
df -h /dev/shm
echo '=== Loaded modules:'
module list 2>&1
"

# Wait for it to finish (usually under 1 minute), then read output:
# squeue --me   # watch until job disappears
# cat /tmp/node_probe_JOBID.out
```

Record from the output:
- **RAM**: the `Mem:` total line from `free -h` → set as `MEM_PER_NODE_GB`
- **CPUs**: `nproc` output → set as `CORES_PER_NODE`
- **Node name**: `hostname` output → needed for `--nodelist` in experiment jobs
- **Local SSD path**: whichever of `/local/scratch`, `/nvme`, etc. exists and has space
- **Shared FS path**: from `df -hT` output (beegfs/lustre/gpfs line)

### Find storage paths (head node only — verify on compute node via probe job above)

```bash
# Shared file system is usually visible from head node too
df -hT 2>/dev/null | grep -E "beegfs|lustre|gpfs|nfs|panfs"
# Common shared paths: /rcfs/projects/*, /global/project/*, /lustre/*, /gpfs/*

# Note: LOCAL_SSD_PATH and TMPFS_PATH must be verified on a compute node.
# The probe job above checks these — do not assume head node mounts match compute nodes.
```

### Find software modules

```bash
# List available ADIOS2 modules
module avail adios 2>&1 | head -20
module avail adios2 2>&1 | head -20

# List Python / conda modules
module avail python 2>&1 | head -20
module avail conda 2>&1 | head -20
module avail anaconda 2>&1 | head -20
```

### Check your existing conda/venv environments

```bash
conda env list 2>/dev/null
ls ~/.conda/envs/ 2>/dev/null
ls ~/miniconda*/envs/ 2>/dev/null
ls ~/anaconda*/envs/ 2>/dev/null
```

---

## Step 1: Fill in config.env

```bash
cd /path/to/wfbench_adios_dpm/
cp config.env.template config.env
nano config.env   # or vim / emacs
```

Replace every `TODO` with values discovered in Step 0. Example filled config:

```bash
CLUSTER_NAME="deception"
PARTITION="compute"
NODES=4
CORES_PER_NODE=40
MEM_PER_NODE_GB=384

LOCAL_SSD_PATH="/local/scratch"
BEEGFS_PATH="/rcfs/projects/YOUR_PROJECT"
TMPFS_PATH="/dev/shm"

ADIOS2_MODULE="adios2/2.9.1-openmpi4"
PYTHON_ENV="/path/to/your/.venv"

DPM_PROFILE_DIR=""   # leave empty first time
```

**Do not commit config.env** — it is in `.gitignore` because it contains cluster-specific paths.

---

## Step 2: Set Up Python Environment

### Option A: Use existing conda env (preferred if ADIOS2 already installed)

```bash
module load ADIOS2_MODULE_NAME   # from config.env ADIOS2_MODULE
conda activate YOUR_ENV
pip install wfcommons>=1.4
python -c "import adios2; import wfcommons; print('OK')"
```

### Option B: Create new conda env

```bash
module load python/3.11          # or anaconda/...
conda create -n dpm_wfbench python=3.11 -y
conda activate dpm_wfbench
pip install wfcommons>=1.4 mpi4py

# Then load ADIOS2 module on top (if available as a system module)
module load adios2/...
python -c "import adios2; print(adios2.__version__)"
```

### Option C: Use system ADIOS2 Python bindings (no module)

```bash
# If ADIOS2 is installed system-wide:
find /usr /opt /sw /apps -name "adios2*" -name "*.py" 2>/dev/null | head -10

# Add to PYTHONPATH if found:
export PYTHONPATH=/path/to/adios2/python/lib:$PYTHONPATH
```

After setup, set `PYTHON_ENV` in config.env to the path of your activated environment:

```bash
PYTHON_ENV=$(conda info --base)/envs/dpm_wfbench
# or
PYTHON_ENV=$(python -c "import sys; print(sys.prefix)")
```

---

## Step 3: Generate Workflow JSON Files

```bash
source config.env          # loads MEM_PER_NODE_GB
cd wfbench/
python generate_workflow.py --size small   # ~5% of node RAM
python generate_workflow.py --size medium  # ~30% of node RAM
python generate_workflow.py --size large   # ~80% of node RAM (ADIOS SST should fail here)
ls -lh workflow_*.json     # confirm created
```

The generator reads `MEM_PER_NODE_GB` from environment to set absolute data sizes.
If that variable is not set, it defaults to 128 GB.

---

## Step 4: Verify Slurm Setup Before Submitting

Check that you can submit a test job before running the real experiments:

```bash
# Simple test job — prints node info
sbatch --partition=PARTITION --nodes=1 --ntasks=1 --time=00:05:00 \
  --account=ACCOUNT_NAME \
  --wrap="hostname; nproc; free -h; df -h /dev/shm"

# Watch it:
squeue --me
```

If `--account` is required (most PNNL clusters require this), add it to the Slurm
header in `scripts/run_adios_sst.sh` and `scripts/run_storage.sh`:

```bash
# Find the line:
# TODO: add --account, --reservation, or other cluster-specific flags
# Replace with:
#SBATCH --account=YOUR_ACCOUNT
```

---

## Step 5: Run the Experiments

### Recommended order (start small, verify, scale up)

```bash
# Test 1: Small data with ADIOS SST (should succeed)
bash scripts/run_adios_sst.sh --size small --nodes 4

# Test 2: Small data with file-based storage (should succeed)
bash scripts/run_storage.sh --size small --storage tmpfs --nodes 4
bash scripts/run_storage.sh --size small --storage ssd   --nodes 4

# Monitor jobs:
squeue --me
tail -f results/*/slurm_*.out

# Once small works, run medium and large:
bash scripts/run_adios_sst.sh --size medium --nodes 4
bash scripts/run_adios_sst.sh --size large  --nodes 4   # expected to fail

bash scripts/run_storage.sh --size large --storage ssd    --nodes 4
bash scripts/run_storage.sh --size large --storage beegfs --nodes 4
```

### Check results as they finish

```bash
# Each completed run writes: results/{run_id}/result.txt
cat results/*/result.txt

# Collect all into a single CSV:
bash scripts/collect_results.sh

# Generate comparison table and plot:
python analysis/compare_results.py \
  --results results/all_results.csv \
  --output  results/
```

---

## Step 6: Troubleshooting

### Job never starts (PENDING forever)

```bash
squeue --me -o "%T %R %j"   # shows reason
# Common reasons: QOSMaxCpuPerUserLimit, AssocGrpCpuLimit, partition unavailable
# Fix: check available partitions with sinfo; check account limits with sacctmgr
```

### ADIOS2 not found at runtime

```bash
# In slurm output, you'll see: ModuleNotFoundError: No module named 'adios2'
# Fix: add module load line to job script, or activate conda env before job
# Edit run_adios_sst.sh:
#   source ${PYTHON_ENV}/bin/activate  <-- already there
# Verify PYTHON_ENV path is correct in config.env
```

### Local SSD path does not exist on compute nodes

```bash
# The LOCAL_SSD_PATH must be accessible from compute nodes (not just login node)
# Test from a job:
sbatch --partition=PARTITION --nodes=1 --wrap="ls -la /local/scratch || echo MISSING"
```

### ADIOS SST connection timeout

```bash
# This is expected behavior for large data or time-decoupled execution.
# The consumer_task.py catches adios2.error.exception and records status=OOM_OR_TIMEOUT
# Check: results/{run_id}/consumer_*.log
```

### Out of memory (OOM) on compute node

```bash
# dmesg or slurm output will show: Killed process ... Out of memory
# consumer_task.py catches MemoryError and records status=OOM
# This is the expected ADIOS SST failure mode for large data
```

---

## Slurm Account and Partition Quick Reference

Once you discover your cluster's values (Step 0), record them here for reference:

| Variable              | Value (fill in) | Source                        |
|-----------------------|-----------------|-------------------------------|
| Cluster name          | TODO            | hostname on login node        |
| Partition             | TODO            | sinfo                         |
| Account               | TODO            | sacctmgr / groups             |
| Example node name     | TODO            | sinfo -o "%N" (for probe job) |
| Nodes available       | TODO            | sinfo                         |
| Cores per node        | TODO            | probe job: nproc              |
| RAM per node          | TODO GB         | probe job: free -h            |
| Local SSD path        | TODO            | probe job: ls /local /nvme    |
| Local SSD capacity    | TODO GB         | probe job: df -h              |
| Shared FS path        | TODO            | df -hT on login node          |
| TMPFS size (/dev/shm) | TODO GB         | probe job: df -h /dev/shm     |
| ADIOS2 module         | TODO            | module avail adios2           |
| Conda env path        | TODO            | conda env list                |

---

## What Success Looks Like

After all experiments complete, `results/all_results.csv` should show:

| size   | backend   | total_time_s | status  |
|--------|-----------|-------------|---------|
| small  | adios_sst | ~Xs         | SUCCESS |
| small  | ssd       | ~Xs         | SUCCESS |
| medium | adios_sst | ~Xs         | SUCCESS |
| medium | ssd       | ~Xs         | SUCCESS |
| large  | adios_sst | —           | FAILED  |  ← expected
| large  | ssd       | ~Xs         | SUCCESS |
| large  | beegfs    | ~Xs         | SUCCESS |

The FAILED row for `large/adios_sst` is the key result: DPM's storage selection
avoids this failure, while ADIOS SST cannot handle time-decoupled large-data workflows.
