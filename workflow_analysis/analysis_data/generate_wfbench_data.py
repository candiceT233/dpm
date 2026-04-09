#!/usr/bin/env python3
"""
Generate wfbench I/O pattern CSV for DPM analysis.

Since wfbench uses IOR with known parameters, we can construct the I/O
pattern table directly from the workflow specification. This matches the
schema of 1kg_workflow_data.csv, pyflex_240f_workflow_data.csv, etc.

The key I/O parameters from run_storage.sh:
  Stage 1: IOR -w -t 1m -b STAGE1_MB  (sequential write, 1MB xfer)
  Stage 2: IOR -r -t 1m -b STAGE2_MB  (sequential read, 1MB xfer)
           IOR -w -t 1m -b STAGE2_MB  (sequential write, 1MB xfer)
  Stage 3: cat (sequential read + write, ~1MB effective xfer)

Data sizes from generate_workflow.py:
  small:  mem_per_node * 0.05 = 384 * 0.05 = 19.2 GB/task
  medium: mem_per_node * 0.30 = 384 * 0.30 = 115.2 GB/task
  large:  mem_per_node * 0.80 = 384 * 0.80 = 307.2 GB/task
  Stage 2 = Stage 1 * 0.125
  Stage 3 = 100 MB (fixed)

Usage:
    python generate_wfbench_data.py [--size small|medium|large] [--output wfbench_workflow_data.csv]
"""

import csv
import argparse
import os

# ── Constants from wfbench experiment ────────────────────────────────────────
MEM_PER_NODE_GB = 384.0
TASKS_PER_NODE = 2
TRANSFER_SIZE_BYTES = 1 * 1024 * 1024  # 1 MB for IOR
REDUCTION_RATIO = 0.125
STAGE3_FILE_BYTES = 100 * 1024 * 1024  # 100 MB fixed

SIZE_FRACTIONS = {
    "small": 0.05,
    "medium": 0.30,
    "large": 0.80,
}

# Node configurations tested
NUM_NODES_LIST = [8, 16]
NUM_NODES_LIST_STR = str(NUM_NODES_LIST)

# Storage type label (pfs = parallel filesystem, matching existing data)
STORAGE_TYPE = "pfs"

COLUMNS = [
    'operation', 'randomOffset', 'transferSize', 'aggregateFilesizeMB',
    'numTasks', 'parallelism', 'totalTime', 'numNodesList', 'numNodes',
    'tasksPerNode', 'trMiB', 'storageType', 'opCount', 'taskName',
    'taskPID', 'fileName', 'stageOrder', 'prevTask'
]


def compute_io_time_estimate(file_size_bytes, transfer_size_bytes, sequential=True):
    """Estimate I/O time based on typical IOR throughput on BeeGFS.

    Uses conservative BeeGFS throughput estimates:
      Sequential write: ~2000 MiB/s per task
      Sequential read:  ~2500 MiB/s per task
    These are rough estimates — DPM will use its own surrogate model,
    so the exact values here don't matter much. What matters is the
    file size and transfer size ratio (opCount).
    """
    file_size_mib = file_size_bytes / (1024 ** 2)
    if sequential:
        throughput_mibs = 2000.0  # conservative estimate
    else:
        throughput_mibs = 2500.0
    time_s = file_size_mib / throughput_mibs
    return max(time_s, 1e-6)


def generate_rows(size_config):
    """Generate all I/O pattern rows for a given size configuration."""
    frac = SIZE_FRACTIONS[size_config]
    stage1_bytes = int(MEM_PER_NODE_GB * frac * 1024 ** 3)
    stage2_bytes = int(stage1_bytes * REDUCTION_RATIO)
    stage3_bytes = STAGE3_FILE_BYTES

    stage1_mb = stage1_bytes / (1024 ** 2)
    stage2_mb = stage2_bytes / (1024 ** 2)
    stage3_mb = stage3_bytes / (1024 ** 2)

    rows = []

    for num_nodes in NUM_NODES_LIST:
        n_tasks = num_nodes * TASKS_PER_NODE
        tpn = TASKS_PER_NODE

        # ── Stage 1: sim tasks — sequential write ────────────────────────
        # One output file per task
        s1_opcount = stage1_bytes // TRANSFER_SIZE_BYTES
        s1_time = compute_io_time_estimate(stage1_bytes, TRANSFER_SIZE_BYTES, sequential=True)
        s1_throughput = (stage1_mb * 1024) / s1_time / 1024  # back to MiB/s

        for i in range(n_tasks):
            rows.append({
                'operation': 'write',
                'randomOffset': 0,  # sequential
                'transferSize': float(TRANSFER_SIZE_BYTES),
                'aggregateFilesizeMB': stage1_mb,
                'numTasks': n_tasks,
                'parallelism': n_tasks,
                'totalTime': s1_time,
                'numNodesList': NUM_NODES_LIST_STR,
                'numNodes': num_nodes,
                'tasksPerNode': tpn,
                'trMiB': s1_throughput,
                'storageType': STORAGE_TYPE,
                'opCount': s1_opcount,
                'taskName': 'sim',
                'taskPID': f'sim_{i}-node{i // tpn}',
                'fileName': f'sim_out_{i}.bin',
                'stageOrder': 1,
                'prevTask': '',
            })

        # ── Stage 2: analysis tasks — sequential read + sequential write ─
        # Read: reads Stage 1 output (STAGE2_MB worth via IOR -b)
        # Write: writes reduced output
        s2_read_opcount = stage2_bytes // TRANSFER_SIZE_BYTES
        s2_read_time = compute_io_time_estimate(stage2_bytes, TRANSFER_SIZE_BYTES, sequential=True)
        s2_read_throughput = (stage2_mb * 1024) / s2_read_time / 1024

        s2_write_opcount = stage2_bytes // TRANSFER_SIZE_BYTES
        s2_write_time = compute_io_time_estimate(stage2_bytes, TRANSFER_SIZE_BYTES, sequential=True)
        s2_write_throughput = (stage2_mb * 1024) / s2_write_time / 1024

        for i in range(n_tasks):
            # Read from Stage 1 output
            rows.append({
                'operation': 'read',
                'randomOffset': 0,  # IOR uses sequential read (-t 1m)
                'transferSize': float(TRANSFER_SIZE_BYTES),
                'aggregateFilesizeMB': stage2_mb,
                'numTasks': n_tasks,
                'parallelism': n_tasks,
                'totalTime': s2_read_time,
                'numNodesList': NUM_NODES_LIST_STR,
                'numNodes': num_nodes,
                'tasksPerNode': tpn,
                'trMiB': s2_read_throughput,
                'storageType': STORAGE_TYPE,
                'opCount': s2_read_opcount,
                'taskName': 'analysis',
                'taskPID': f'analysis_{i}-node{i // tpn}',
                'fileName': f'sim_out_{i}.bin',
                'stageOrder': 2,
                'prevTask': 'sim',
            })
            # Write reduced output
            rows.append({
                'operation': 'write',
                'randomOffset': 0,  # sequential
                'transferSize': float(TRANSFER_SIZE_BYTES),
                'aggregateFilesizeMB': stage2_mb,
                'numTasks': n_tasks,
                'parallelism': n_tasks,
                'totalTime': s2_write_time,
                'numNodesList': NUM_NODES_LIST_STR,
                'numNodes': num_nodes,
                'tasksPerNode': tpn,
                'trMiB': s2_write_throughput,
                'storageType': STORAGE_TYPE,
                'opCount': s2_write_opcount,
                'taskName': 'analysis',
                'taskPID': f'analysis_{i}-node{i // tpn}',
                'fileName': f'analysis_out_{i}.bin',
                'stageOrder': 2,
                'prevTask': 'sim',
            })

        # ── Stage 3: aggregate — sequential read all + write summary ─────
        # Reads all Stage 2 outputs (N files of stage2_mb each)
        total_agg_input_mb = stage2_mb * n_tasks
        s3_read_opcount = int(total_agg_input_mb * 1024 * 1024) // TRANSFER_SIZE_BYTES
        s3_read_time = compute_io_time_estimate(
            int(total_agg_input_mb * 1024 * 1024), TRANSFER_SIZE_BYTES, sequential=True)
        s3_read_throughput = (total_agg_input_mb * 1024) / s3_read_time / 1024

        # Read each analysis output file
        for i in range(n_tasks):
            rows.append({
                'operation': 'read',
                'randomOffset': 0,
                'transferSize': float(TRANSFER_SIZE_BYTES),
                'aggregateFilesizeMB': stage2_mb,
                'numTasks': 1,
                'parallelism': 1,
                'totalTime': s3_read_time / n_tasks,  # per-file read time
                'numNodesList': NUM_NODES_LIST_STR,
                'numNodes': num_nodes,
                'tasksPerNode': 1,  # single aggregator
                'trMiB': s3_read_throughput,
                'storageType': STORAGE_TYPE,
                'opCount': s2_write_opcount,  # same as one analysis output
                'taskName': 'aggregate',
                'taskPID': f'aggregate_0-node0',
                'fileName': f'analysis_out_{i}.bin',
                'stageOrder': 3,
                'prevTask': 'analysis',
            })

        # Write summary output
        s3_write_opcount = stage3_bytes // TRANSFER_SIZE_BYTES
        s3_write_time = compute_io_time_estimate(stage3_bytes, TRANSFER_SIZE_BYTES, sequential=True)
        s3_write_throughput = (stage3_mb * 1024) / s3_write_time / 1024

        rows.append({
            'operation': 'write',
            'randomOffset': 0,
            'transferSize': float(TRANSFER_SIZE_BYTES),
            'aggregateFilesizeMB': stage3_mb,
            'numTasks': 1,
            'parallelism': 1,
            'totalTime': s3_write_time,
            'numNodesList': NUM_NODES_LIST_STR,
            'numNodes': num_nodes,
            'tasksPerNode': 1,
            'trMiB': s3_write_throughput,
            'storageType': STORAGE_TYPE,
            'opCount': s3_write_opcount,
            'taskName': 'aggregate',
            'taskPID': f'aggregate_0-node0',
            'fileName': 'aggregate_out.bin',
            'stageOrder': 3,
            'prevTask': 'analysis',
        })

    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--size', choices=['small', 'medium', 'large', 'all'],
                        default='all', help='Data size config (default: all)')
    parser.add_argument('--output', default=None,
                        help='Output CSV path (default: wfbench_{size}_workflow_data.csv)')
    args = parser.parse_args()

    if args.size == 'all':
        sizes = ['small', 'medium', 'large']
    else:
        sizes = [args.size]

    for size in sizes:
        rows = generate_rows(size)
        output_path = args.output or f'wfbench_{size}_workflow_data.csv'
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(rows)

        print(f"Generated {output_path}: {len(rows)} rows "
              f"(size={size}, nodes={NUM_NODES_LIST})")

        # Print summary
        frac = SIZE_FRACTIONS[size]
        s1_bytes = int(MEM_PER_NODE_GB * frac * 1024 ** 3)
        s2_bytes = int(s1_bytes * REDUCTION_RATIO)
        print(f"  Stage 1: {s1_bytes / 1024**3:.1f} GB/task, "
              f"xfer=1MB, sequential write")
        print(f"  Stage 2: {s2_bytes / 1024**3:.1f} GB/task, "
              f"xfer=1MB, sequential read+write")
        print(f"  Stage 3: {STAGE3_FILE_BYTES / 1024**2:.0f} MB output, "
              f"xfer=1MB, sequential read+write")


if __name__ == '__main__':
    main()
