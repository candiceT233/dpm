#!/usr/bin/env python3
"""
compare_results.py — Compare ADIOS SST vs DPM storage results.

Reads all_results.csv and produces:
  1. comparison_table.csv — summary table for the paper
  2. comparison_plot.pdf  — bar chart for the paper figure

Usage:
    python analysis/compare_results.py \
        --results results/all_results.csv \
        --output  results/
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import sys
from pathlib import Path


BACKEND_LABELS = {
    "adios_sst": "ADIOS SST\n(in-situ)",
    "ssd":        "Local SSD\n(DPM)",
    "beegfs":     "BeeGFS\n(DPM)",
    "tmpfs":      "TMPFS\n(DPM)",
}
BACKEND_COLORS = {
    "adios_sst": "#d62728",   # red
    "ssd":        "#2ca02c",   # green
    "beegfs":     "#1f77b4",   # blue
    "tmpfs":      "#ff7f0e",   # orange
}
SIZE_ORDER = ["small", "medium", "large"]


def load_results(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["total_time_s"] = pd.to_numeric(df["total_time_s"], errors="coerce")
    df["failed"] = df["status"].str.upper().isin(["FAILED", "OOM", "TIMEOUT", "NA"])
    return df


def make_table(df: pd.DataFrame, output_dir: Path):
    """Produce a summary table grouped by size and backend."""
    summary = (
        df.groupby(["size", "backend"])
          .agg(
              mean_time=("total_time_s", "mean"),
              std_time=("total_time_s",  "std"),
              n_runs=("total_time_s",    "count"),
              n_failed=("failed",        "sum"),
          )
          .reset_index()
    )
    summary["outcome"] = summary.apply(
        lambda r: "FAILED" if r["n_failed"] > 0 else f"{r['mean_time']:.1f}s ± {r['std_time']:.1f}s",
        axis=1
    )

    pivot = summary.pivot_table(index="size", columns="backend", values="outcome", aggfunc="first")
    pivot = pivot.reindex(SIZE_ORDER)

    out_path = output_dir / "comparison_table.csv"
    pivot.to_csv(out_path)
    print(f"[compare_results] Table written: {out_path}")
    print(pivot.to_string())
    return summary


def make_plot(df: pd.DataFrame, summary: pd.DataFrame, output_dir: Path):
    """Produce a grouped bar chart: x=data size, groups=backend."""
    backends = [b for b in ["adios_sst", "tmpfs", "ssd", "beegfs"] if b in df["backend"].unique()]
    n_sizes = len(SIZE_ORDER)
    n_backends = len(backends)

    fig, ax = plt.subplots(figsize=(10, 5))
    bar_width = 0.8 / n_backends
    x = np.arange(n_sizes)

    for bi, backend in enumerate(backends):
        times = []
        errors = []
        hatches = []
        for size in SIZE_ORDER:
            row = summary[(summary["backend"] == backend) & (summary["size"] == size)]
            if row.empty or row["n_failed"].values[0] > 0:
                times.append(0)
                errors.append(0)
                hatches.append("////")
            else:
                times.append(row["mean_time"].values[0])
                errors.append(row["std_time"].values[0] if not pd.isna(row["std_time"].values[0]) else 0)
                hatches.append("")

        offset = (bi - n_backends / 2 + 0.5) * bar_width
        bars = ax.bar(
            x + offset, times, bar_width * 0.9,
            label=BACKEND_LABELS.get(backend, backend),
            color=BACKEND_COLORS.get(backend, "gray"),
            yerr=errors, capsize=3,
            error_kw={"elinewidth": 1, "alpha": 0.7},
            alpha=0.85
        )
        # Add hatch for failed bars and "FAILED" label
        for bar, hatch, time in zip(bars, hatches, times):
            if hatch:
                bar.set_hatch(hatch)
                bar.set_edgecolor("black")
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    max(summary["mean_time"].dropna()) * 0.05,
                    "FAILED", ha="center", va="bottom",
                    fontsize=7, color="black", fontweight="bold", rotation=90
                )

    ax.set_xticks(x)
    ax.set_xticklabels([f"Data: {s.capitalize()}" for s in SIZE_ORDER], fontsize=11)
    ax.set_ylabel("Total Workflow Time (seconds)", fontsize=11)
    ax.set_title("ADIOS SST vs DPM Storage Selection\n"
                 "Synthetic 3-Stage Producer-Consumer Workflow", fontsize=12)
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(axis="y", alpha=0.3)

    # Annotation explaining failure
    ax.annotate(
        "ADIOS SST fails on large data:\ndata exceeds in-memory buffer capacity\nor time-decoupled batch scheduling",
        xy=(2, ax.get_ylim()[1] * 0.5),
        xytext=(1.5, ax.get_ylim()[1] * 0.7),
        fontsize=8.5, color="#d62728",
        arrowprops=dict(arrowstyle="->", color="#d62728"),
        ha="center"
    )

    plt.tight_layout()
    out_path = output_dir / "comparison_plot.pdf"
    plt.savefig(out_path, bbox_inches="tight")
    print(f"[compare_results] Plot written: {out_path}")
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results/all_results.csv")
    parser.add_argument("--output",  default="results/")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = load_results(args.results)
    if df.empty:
        print("ERROR: No results found in", args.results, file=sys.stderr)
        sys.exit(1)

    print(f"[compare_results] Loaded {len(df)} rows from {args.results}")
    summary = make_table(df, output_dir)
    make_plot(df, summary, output_dir)

    print("\n[compare_results] Done.")


if __name__ == "__main__":
    main()
