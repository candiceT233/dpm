#!/usr/bin/env python3
"""Derive the PyflexTRKR DPM storage-parallelism selection.

This script reads the hardcoded SPM values from the PyflexTRKR plotting script
without importing it, then computes the uniform workflow-level DPM selection.
It exists to make the paper's PyflexTRKR BeeGFS/8n selection reproducible and
to avoid confusing it with the stale runtime-summary CSV that hardcodes TMPFS.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any


DEFAULT_SOURCE = Path("workflow_analysis/spm_figures/spm_figures_pyflex.py")


def _literal_assignment_from_function(
    source: Path, function_name: str, variable_name: str
) -> dict[str, Any]:
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    function = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == function_name
        ),
        None,
    )
    if function is None:
        raise ValueError(f"Function {function_name!r} not found in {source}")

    value: dict[str, Any] | None = None
    for node in ast.walk(function):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == variable_name
            for target in node.targets
        ):
            continue
        try:
            candidate = ast.literal_eval(node.value)
        except (ValueError, SyntaxError):
            continue
        if isinstance(candidate, dict):
            value = candidate

    if value is None:
        raise ValueError(
            f"Literal assignment to {variable_name!r} not found in {function_name!r}"
        )
    return value


def load_spm_data(source: Path) -> dict[str, Any]:
    return _literal_assignment_from_function(source, "create_spm_data", "spm_data")


def uniform_config_totals(spm_data: dict[str, Any]) -> list[dict[str, Any]]:
    configs = spm_data.get("store_conf")
    if not isinstance(configs, list) or not configs:
        raise ValueError("SPM data must include a non-empty store_conf list")

    rows: list[dict[str, Any]] = []
    for index, config in enumerate(configs):
        total = 0.0
        for key, values in spm_data.items():
            if key == "store_conf":
                continue
            if not isinstance(values, list) or len(values) != len(configs):
                raise ValueError(f"SPM values for {key!r} must match store_conf length")
            total += float(values[index])
        rows.append({"config": config, "spm_total": total})
    return sorted(rows, key=lambda row: row["spm_total"])


def per_pair_winners(spm_data: dict[str, Any]) -> list[dict[str, Any]]:
    configs = spm_data["store_conf"]
    rows: list[dict[str, Any]] = []
    for pair, values in spm_data.items():
        if pair == "store_conf":
            continue
        best_index = min(range(len(values)), key=lambda index: float(values[index]))
        rows.append(
            {
                "pair": pair,
                "config": configs[best_index],
                "spm": float(values[best_index]),
            }
        )
    return rows


def derive_selection(source: Path) -> dict[str, Any]:
    spm_data = load_spm_data(source)
    totals = uniform_config_totals(spm_data)
    return {
        "source": str(source),
        "selection": totals[0]["config"],
        "uniform_config_totals": totals,
        "per_pair_winners": per_pair_winners(spm_data),
    }


def _print_markdown(result: dict[str, Any]) -> None:
    print(f"Source: `{result['source']}`")
    print(f"DPM selection: `{result['selection']}`")
    print()
    print("| Uniform config | Sum of SPM values |")
    print("| --- | ---: |")
    for row in result["uniform_config_totals"]:
        print(f"| {row['config']} | {row['spm_total']:.3f} |")
    print()
    print("| Producer-consumer pair | Best config | SPM |")
    print("| --- | --- | ---: |")
    for row in result["per_pair_winners"]:
        print(f"| {row['pair']} | {row['config']} | {row['spm']:.3f} |")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Path to spm_figures_pyflex.py (default: {DEFAULT_SOURCE})",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format",
    )
    parser.add_argument(
        "--expect",
        help="Fail unless the derived DPM selection matches this config",
    )
    args = parser.parse_args()

    result = derive_selection(args.source)
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        _print_markdown(result)

    if args.expect and result["selection"] != args.expect:
        print(
            f"ERROR: expected {args.expect!r}, got {result['selection']!r}",
            flush=True,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
