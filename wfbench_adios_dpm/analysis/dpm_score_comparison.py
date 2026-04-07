#!/usr/bin/env python3
"""
dpm_score_comparison.py — Validate DPM score ranking against actual workflow timing.

For each (data size, storage tier) combination:
  1. Load actual measured total_time_s from all_results.csv
  2. Load DPM scores (estT_prod + estT_cons) from IOR profiling data
  3. Rank tiers by DPM score (ascending) and by actual time (ascending)
  4. Check whether DPM rank matches actual rank

Produces:
  results/dpm_score_ranking.csv   — per-config scores, times, and ranks
  results/ranking_comparison.pdf  — side-by-side DPM score vs actual time

Usage:
    python analysis/dpm_score_comparison.py \
        --results   results/all_results.csv \
        --profiles  /path/to/ior_profiles/ \
        --workflow  wfbench/workflow_large.json \
        --output    results/

NOTE: --profiles must point to a directory containing IOR profiling CSVs
collected on this cluster (e.g. from DPM_PROFILE_DIR in config.env).
If profiles are not yet available, use --scores-csv to provide a manually
prepared DPM scores CSV instead (see --help for format).
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


STORAGE_LABELS = {
    "ssd":    "Local SSD",
    "beegfs": "BeeGFS",
    "tmpfs":  "TMPFS",
}
STORAGE_COLORS = {
    "ssd":    "#2ca02c",
    "beegfs": "#1f77b4",
    "tmpfs":  "#ff7f0e",
}
SIZE_ORDER = ["small", "medium", "large"]


# ---------------------------------------------------------------------------
# Loading helpers
# ---------------------------------------------------------------------------

def load_results(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["total_time_s"] = pd.to_numeric(df["total_time_s"], errors="coerce")
    df["failed"] = df["status"].str.upper().isin(["FAILED", "OOM", "TIMEOUT", "NA"])
    # Exclude adios_sst from ranking comparison — it is a separate baseline
    return df[df["backend"] != "adios_sst"].copy()


def load_dpm_scores_from_profiles(profile_dir: str, workflow_json: str) -> pd.DataFrame:
    """
    Compute DPM scores from IOR profiling CSVs.

    DPM score = estT_prod + estT_cons for each (storage tier, data size) pair.
    estT_prod and estT_cons are predicted from the linear regression model
    using the I/O pattern parameters from the workflow JSON.

    This function is a stub — replace with actual DPM model invocation
    using the workflow_analysis/modules/workflow_dpm_calculator.py logic
    from the main DPM repo. The expected output format is shown below.
    """
    profile_path = Path(profile_dir)
    if not profile_path.exists():
        raise FileNotFoundError(
            f"Profile directory not found: {profile_dir}\n"
            "Provide --profiles pointing to IOR profiling CSVs, or use\n"
            "--scores-csv with a manually prepared DPM scores file."
        )

    # Load workflow I/O pattern parameters
    with open(workflow_json) as f:
        wf = json.load(f)
    meta = wf.get("dpmMeta", {})

    # TODO: invoke DPM model here using workflow_dpm_calculator
    # Expected return: DataFrame with columns [size, backend, dpm_score]
    # Example placeholder:
    raise NotImplementedError(
        "load_dpm_scores_from_profiles: connect DPM model here.\n"
        "Use --scores-csv to provide pre-computed DPM scores instead."
    )


def load_dpm_scores_from_csv(scores_csv: str) -> pd.DataFrame:
    """
    Load pre-computed DPM scores from a CSV file.

    Expected columns: size, backend, dpm_score
    Where dpm_score = estT_prod + estT_cons (predicted seconds, lower = better).

    Example scores CSV:
        size,backend,dpm_score
        small,tmpfs,12.3
        small,ssd,18.7
        small,beegfs,34.1
        medium,ssd,45.2
        medium,beegfs,61.8
        medium,tmpfs,999
        large,ssd,120.4
        large,beegfs,158.9
        large,tmpfs,999
    """
    df = pd.read_csv(scores_csv)
    required = {"size", "backend", "dpm_score"}
    missing = required - set(df.columns)
    if missing:
        print(f"ERROR: scores CSV missing columns: {missing}", file=sys.stderr)
        sys.exit(1)
    df["dpm_score"] = pd.to_numeric(df["dpm_score"], errors="coerce")
    return df


# ---------------------------------------------------------------------------
# Ranking and comparison
# ---------------------------------------------------------------------------

def build_ranking_table(results_df: pd.DataFrame, scores_df: pd.DataFrame) -> pd.DataFrame:
    """
    For each (size, backend): compute mean actual time, DPM score, and both ranks.
    """
    # Aggregate actual timing
    actual = (
        results_df[~results_df["failed"]]
        .groupby(["size", "backend"])
        .agg(mean_time=("total_time_s", "mean"), std_time=("total_time_s", "std"))
        .reset_index()
    )
    # Mark failed configs
    failed = (
        results_df[results_df["failed"]]
        .groupby(["size", "backend"])
        .size()
        .reset_index(name="n_failed")
    )

    merged = actual.merge(scores_df[["size", "backend", "dpm_score"]], on=["size", "backend"], how="outer")
    merged = merged.merge(failed, on=["size", "backend"], how="left")
    merged["n_failed"] = merged["n_failed"].fillna(0).astype(int)
    merged["failed"] = merged["n_failed"] > 0

    rows = []
    for size in SIZE_ORDER:
        subset = merged[merged["size"] == size].copy()
        if subset.empty:
            continue

        # Rank by DPM score (lower = better; NaN/failed = last)
        subset["dpm_rank"] = subset["dpm_score"].rank(method="min", na_option="bottom").astype(int)

        # Rank by actual time (lower = better; failed = last)
        valid = subset[~subset["failed"]].copy()
        valid["actual_rank"] = valid["mean_time"].rank(method="min").astype(int)
        subset = subset.merge(valid[["backend", "actual_rank"]], on="backend", how="left")
        subset.loc[subset["failed"], "actual_rank"] = len(subset)

        subset["ranks_match"] = (
            subset["dpm_rank"] == subset["actual_rank"]
        ).where(~subset["failed"], other=pd.NA)

        rows.append(subset)

    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_csv(ranking: pd.DataFrame, output_dir: Path):
    cols = ["size", "backend", "dpm_score", "dpm_rank", "mean_time", "std_time", "actual_rank", "ranks_match", "failed"]
    out = output_dir / "dpm_score_ranking.csv"
    ranking[cols].sort_values(["size", "dpm_rank"]).to_csv(out, index=False)
    print(f"[dpm_score_comparison] Ranking table: {out}")
    print(ranking[cols].sort_values(["size", "dpm_rank"]).to_string(index=False))


def write_plot(ranking: pd.DataFrame, output_dir: Path):
    backends = [b for b in ["tmpfs", "ssd", "beegfs"] if b in ranking["backend"].unique()]
    n_sizes = len(SIZE_ORDER)
    n_backends = len(backends)
    bar_width = 0.35 / n_backends

    fig, (ax_score, ax_time) = plt.subplots(1, 2, figsize=(13, 5))
    x = np.arange(n_sizes)

    for bi, backend in enumerate(backends):
        scores, times, score_errs, time_errs = [], [], [], []
        for size in SIZE_ORDER:
            row = ranking[(ranking["backend"] == backend) & (ranking["size"] == size)]
            if row.empty or row["failed"].values[0]:
                scores.append(0); score_errs.append(0)
                times.append(0);  time_errs.append(0)
            else:
                scores.append(row["dpm_score"].values[0])
                score_errs.append(0)  # DPM score is a point estimate
                times.append(row["mean_time"].values[0])
                te = row["std_time"].values[0]
                time_errs.append(te if not pd.isna(te) else 0)

        offset = (bi - n_backends / 2 + 0.5) * bar_width * 2
        color = STORAGE_COLORS.get(backend, "gray")
        label = STORAGE_LABELS.get(backend, backend)

        ax_score.bar(x + offset, scores, bar_width * 1.8, label=label, color=color, alpha=0.85)
        ax_time.bar(x + offset, times, bar_width * 1.8, label=label, color=color, alpha=0.85,
                    yerr=time_errs, capsize=3, error_kw={"elinewidth": 1, "alpha": 0.7})

    for ax, title, ylabel in [
        (ax_score, "DPM Score by Storage Tier\n(lower = DPM recommends)", "DPM Score (predicted seconds)"),
        (ax_time,  "Actual Workflow Time by Storage Tier\n(lower = actually faster)", "Total Workflow Time (seconds)"),
    ]:
        ax.set_xticks(x)
        ax.set_xticklabels([s.capitalize() for s in SIZE_ORDER], fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_title(title, fontsize=11)
        ax.legend(loc="upper left", framealpha=0.9)
        ax.grid(axis="y", alpha=0.3)

    # Annotate matching ranks
    n_match = ranking["ranks_match"].sum()
    n_total = ranking["ranks_match"].notna().sum()
    fig.suptitle(
        f"DPM Score Rank vs Actual Rank — {n_match}/{n_total} configurations matched",
        fontsize=12, fontweight="bold"
    )

    plt.tight_layout()
    out = output_dir / "ranking_comparison.pdf"
    plt.savefig(out, bbox_inches="tight")
    print(f"[dpm_score_comparison] Plot: {out}")
    plt.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results",    required=True, help="Path to all_results.csv")
    parser.add_argument("--output",     default="results/", help="Output directory")
    parser.add_argument("--workflow",   default="wfbench/workflow_large.json",
                        help="Workflow JSON (for I/O pattern parameters)")
    # Two ways to provide DPM scores:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--profiles",   help="Directory with IOR profiling CSVs (computes DPM scores)")
    group.add_argument("--scores-csv", help="Pre-computed DPM scores CSV (size,backend,dpm_score)")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = load_results(args.results)
    if results.empty:
        print("ERROR: No non-ADIOS results in", args.results, file=sys.stderr)
        sys.exit(1)

    if args.scores_csv:
        scores = load_dpm_scores_from_csv(args.scores_csv)
    else:
        scores = load_dpm_scores_from_profiles(args.profiles, args.workflow)

    ranking = build_ranking_table(results, scores)
    if ranking.empty:
        print("ERROR: Could not build ranking table — check that results and scores share (size, backend) keys.",
              file=sys.stderr)
        sys.exit(1)

    write_csv(ranking, output_dir)
    write_plot(ranking, output_dir)

    n_match = ranking["ranks_match"].sum()
    n_total = ranking["ranks_match"].notna().sum()
    print(f"\n[dpm_score_comparison] DPM rank matches actual rank: {n_match}/{n_total}")
    if n_match == n_total:
        print("[dpm_score_comparison] RESULT: DPM correctly ranked all storage tiers.")
    else:
        print("[dpm_score_comparison] RESULT: Some rankings did not match — see dpm_score_ranking.csv.")


if __name__ == "__main__":
    main()
