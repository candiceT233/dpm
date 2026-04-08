#!/usr/bin/env python3
"""
compare_results.py — Analyze Montage DPM evaluation results

Reads collected CSV results and produces:
1. Per-stage timing breakdown by storage and node count
2. Ranking comparison table (DPM predicted vs actual)
3. Bar chart of total workflow runtime across configurations

Usage:
    python analysis/compare_results.py --results results/all_results.csv
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def load_results(csv_path):
    df = pd.read_csv(csv_path)
    df = df[df["status"] == "SUCCESS"]
    return df


def ranking_table(df):
    """Compute actual runtime rankings per (size, nodes) group."""
    rankings = []
    for (size, nodes), group in df.groupby(["size", "nodes"]):
        mean_times = group.groupby("backend")["total_time_s"].mean().sort_values()
        for rank, (backend, time) in enumerate(mean_times.items(), 1):
            rankings.append({
                "size": size,
                "nodes": nodes,
                "backend": backend,
                "actual_rank": rank,
                "mean_time_s": round(time, 2),
            })
    return pd.DataFrame(rankings)


def plot_runtime_comparison(df, output_path):
    """Bar chart: total runtime by storage and node count."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharey=True)
    storages = sorted(df["backend"].unique())
    node_counts = sorted(df["nodes"].unique())
    colors = {"ssd": "#2196F3", "beegfs": "#FF9800", "tmpfs": "#4CAF50"}
    x = np.arange(len(node_counts))
    width = 0.25

    for ax_idx, size in enumerate(sorted(df["size"].unique())):
        ax = axes[ax_idx] if len(axes) > 1 else axes
        subset = df[df["size"] == size]
        for i, storage in enumerate(storages):
            means = []
            stds = []
            for nodes in node_counts:
                data = subset[(subset["backend"] == storage) & (subset["nodes"] == nodes)]["total_time_s"]
                means.append(data.mean() if len(data) > 0 else 0)
                stds.append(data.std() if len(data) > 1 else 0)
            ax.bar(x + i * width, means, width, yerr=stds, label=storage,
                   color=colors.get(storage, "#999"), capsize=3)
        ax.set_title(f"{size} dataset")
        ax.set_xlabel("Nodes")
        ax.set_xticks(x + width)
        ax.set_xticklabels(node_counts)
        if ax_idx == 0:
            ax.set_ylabel("Total Runtime (s)")
        ax.legend()

    plt.suptitle("Montage Workflow Runtime: Storage × Parallelism")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {output_path}")


def plot_stage_breakdown(df, output_path):
    """Stacked bar: per-stage timing for each configuration."""
    stage_cols = [c for c in df.columns if c.endswith("_s") and c != "total_time_s"]
    if not stage_cols:
        print("No per-stage timing columns found, skipping breakdown plot")
        return

    means = df.groupby(["backend", "nodes"])[stage_cols].mean()
    means.plot(kind="bar", stacked=True, figsize=(12, 6), colormap="tab10")
    plt.title("Montage Per-Stage Timing Breakdown")
    plt.xlabel("(Storage, Nodes)")
    plt.ylabel("Time (s)")
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Analyze Montage DPM results")
    parser.add_argument("--results", default="results/all_results.csv")
    parser.add_argument("--output", default="results/")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = load_results(args.results)
    print(f"Loaded {len(df)} successful runs")
    print(f"Configurations: {df.groupby(['backend', 'nodes']).ngroups}")
    print()

    # Ranking table
    rankings = ranking_table(df)
    print("=== Actual Runtime Rankings ===")
    print(rankings.to_string(index=False))
    rankings.to_csv(output_dir / "ranking_table.csv", index=False)
    print()

    # Plots
    plot_runtime_comparison(df, output_dir / "montage_runtime_comparison.pdf")
    plot_stage_breakdown(df, output_dir / "montage_stage_breakdown.pdf")


if __name__ == "__main__":
    main()
