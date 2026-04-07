#!/usr/bin/env python3
"""
Generate WfBench synthetic workflows for the ADIOS vs DPM comparison.

Usage:
    python generate_workflow.py --size small  --nodes 4 --mem-per-node 384
    python generate_workflow.py --size medium --nodes 4 --mem-per-node 384
    python generate_workflow.py --size large  --nodes 4 --mem-per-node 384

Produces a WfFormat JSON workflow file that WfBench can execute.
"""

import argparse
import json
import math
import os
import sys
from pathlib import Path

# ── Data size fractions of per-node memory ──────────────────────────────────
SIZE_FRACTIONS = {
    "small":  0.05,   # 5% of node RAM per task → fits in memory easily
    "medium": 0.30,   # 30% of node RAM per task → borderline
    "large":  0.80,   # 80% of node RAM per task → exceeds memory when multiple tasks share
}

# Stage 2 output is this fraction of Stage 1 output
REDUCTION_RATIO = 0.125   # 1/8 reduction


def bytes_to_human(b):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def generate_workflow(size: str, nodes: int, tasks_per_node: int,
                      mem_per_node_gb: float) -> dict:
    """
    Build a WfFormat v1.5 workflow JSON.

    Topology:
        Stage 1 (sim):       N parallel tasks, each writes 1 large file
        Stage 2 (analysis):  N parallel tasks, each reads 1 Stage1 file, writes smaller
        Stage 3 (aggregate): 1 task reads all Stage2 files, writes summary
    """
    n_tasks = nodes * tasks_per_node
    frac = SIZE_FRACTIONS[size]

    # File sizes in bytes
    stage1_file_bytes = int(mem_per_node_gb * frac * 1024**3)  # per task
    stage2_file_bytes = int(stage1_file_bytes * REDUCTION_RATIO)
    stage3_file_bytes = int(100 * 1024**2)  # fixed 100MB summary

    print(f"[generate_workflow] size={size}, nodes={nodes}, tasks={n_tasks}")
    print(f"  Stage 1 output per task: {bytes_to_human(stage1_file_bytes)}")
    print(f"  Stage 2 output per task: {bytes_to_human(stage2_file_bytes)}")
    print(f"  Stage 3 output: {bytes_to_human(stage3_file_bytes)}")
    print(f"  Total intermediate data: {bytes_to_human(stage1_file_bytes * n_tasks)}")

    tasks = []
    files = []
    file_id = 0

    # ── Stage 1: sim tasks (sequential write, I/O-heavy) ────────────────────
    stage1_output_file_ids = []
    for i in range(n_tasks):
        out_file_id = f"sim_out_{i}"
        stage1_output_file_ids.append(out_file_id)
        files.append({
            "id": out_file_id,
            "sizeInBytes": stage1_file_bytes,
            "link": "output"
        })
        tasks.append({
            "name": f"sim_{i}",
            "id": f"sim_{i}",
            "category": "sim",
            "type": "compute",
            "parents": [],
            "inputFiles": [],
            "outputFiles": [{"id": out_file_id, "sizeInBytes": stage1_file_bytes}],
            # I/O pattern: sequential write, 1MB transfer size
            "ioPattern": "sequential_write",
            "transferSizeMB": 1,
            # Runtime estimate: 95% I/O-bound
            "runtimeInSeconds": max(10, int(stage1_file_bytes / (500 * 1024**2))),
            "avgCPU": 0.05,
            "memoryInBytes": int(stage1_file_bytes * 0.1),  # small working set
        })

    # ── Stage 2: analysis tasks (random read + sequential write) ────────────
    stage2_output_file_ids = []
    for i in range(n_tasks):
        in_file_id = stage1_output_file_ids[i]
        out_file_id = f"analysis_out_{i}"
        stage2_output_file_ids.append(out_file_id)
        files.append({
            "id": out_file_id,
            "sizeInBytes": stage2_file_bytes,
            "link": "output"
        })
        tasks.append({
            "name": f"analysis_{i}",
            "id": f"analysis_{i}",
            "category": "analysis",
            "type": "compute",
            "parents": [f"sim_{i}"],
            "inputFiles": [{"id": in_file_id, "sizeInBytes": stage1_file_bytes}],
            "outputFiles": [{"id": out_file_id, "sizeInBytes": stage2_file_bytes}],
            # I/O pattern: random read (4KB), then sequential write (1MB)
            "ioPattern": "random_read",
            "transferSizeMB": 0.004,  # 4KB random reads
            "runtimeInSeconds": max(10, int(stage1_file_bytes / (200 * 1024**2))),
            "avgCPU": 0.30,
            "memoryInBytes": int(256 * 1024**2),  # 256MB working set
        })

    # ── Stage 3: aggregate task (sequential read + write) ───────────────────
    agg_in_files = [
        {"id": fid, "sizeInBytes": stage2_file_bytes}
        for fid in stage2_output_file_ids
    ]
    agg_out_id = "aggregate_out"
    files.append({"id": agg_out_id, "sizeInBytes": stage3_file_bytes, "link": "output"})
    tasks.append({
        "name": "aggregate_0",
        "id": "aggregate_0",
        "category": "aggregate",
        "type": "compute",
        "parents": [f"analysis_{i}" for i in range(n_tasks)],
        "inputFiles": agg_in_files,
        "outputFiles": [{"id": agg_out_id, "sizeInBytes": stage3_file_bytes}],
        "ioPattern": "sequential_read",
        "transferSizeMB": 1,
        "runtimeInSeconds": max(5, int(stage2_file_bytes * n_tasks / (1000 * 1024**2))),
        "avgCPU": 0.50,
        "memoryInBytes": int(1024 * 1024**2),  # 1GB working set
    })

    workflow = {
        "name": f"wfbench-adios-dpm-{size}",
        "description": (
            f"Synthetic 3-stage producer-consumer workflow for ADIOS vs DPM comparison. "
            f"Size={size}, nodes={nodes}, tasks={n_tasks}, "
            f"intermediate_data={bytes_to_human(stage1_file_bytes * n_tasks)}"
        ),
        "schemaVersion": "1.5",
        "createdAt": "2026-04-06",
        "author": {
            "name": "DPM Paper Experiment",
            "email": "TODO"
        },
        "workflow": {
            "specification": {
                "tasks": tasks,
                "files": files,
            },
            "execution": {
                "makespanInSeconds": None,  # filled after run
            }
        },
        # Metadata for DPM profiling
        "dpmMeta": {
            "sizeConfig": size,
            "nodes": nodes,
            "tasksPerNode": tasks_per_node,
            "memPerNodeGB": mem_per_node_gb,
            "stage1FileSizeBytes": stage1_file_bytes,
            "stage2FileSizeBytes": stage2_file_bytes,
            "totalIntermediateBytes": stage1_file_bytes * n_tasks,
            "adiosExpectedOutcome": {
                "small": "success",
                "medium": "marginal",
                "large": "fail_oom_or_timeout"
            }[size],
        }
    }

    return workflow


def main():
    parser = argparse.ArgumentParser(
        description="Generate WfBench workflow JSON for ADIOS vs DPM experiment"
    )
    parser.add_argument("--size", choices=["small", "medium", "large"], required=True)
    parser.add_argument("--nodes", type=int, default=4)
    parser.add_argument("--tasks-per-node", type=int,
                        default=int(os.environ.get("TASKS_PER_NODE", 2)))
    parser.add_argument("--mem-per-node", type=float,
                        default=float(os.environ.get("MEM_PER_NODE_GB", 384.0)),
                        help="Node RAM in GB (reads MEM_PER_NODE_GB from env if not set)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output JSON file (default: workflow_{size}_{nodes}n.json)")
    args = parser.parse_args()

    # Include node count in filename so phase 3 scaling runs have separate JSONs
    output_file = args.output or f"workflow_{args.size}_{args.nodes}n.json"

    workflow = generate_workflow(
        size=args.size,
        nodes=args.nodes,
        tasks_per_node=args.tasks_per_node,
        mem_per_node_gb=args.mem_per_node,
    )

    out_path = Path(output_file)
    out_path.write_text(json.dumps(workflow, indent=2))
    print(f"[generate_workflow] Written: {out_path}")
    print(f"  Total tasks: {len(workflow['workflow']['specification']['tasks'])}")
    print(f"  Total files: {len(workflow['workflow']['specification']['files'])}")


if __name__ == "__main__":
    main()
