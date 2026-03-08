"""
Config-driven path/effect size analysis and heatmap orchestration.

Reads pathsdata.json and PATHS config section, then calls
viz/plots.py functions to produce batch outputs.

Ported from cda_tools2's paths_plotdist2.py (PathsPlot class).
"""

import glob
import json
import os
from typing import Any, Optional

import numpy as np
import pandas as pd

from fastcausal.pipeline.config import get_output_dir, get_project_dir


def run_paths(cfg: dict, verbose: bool = True):
    """
    Run path/effect size analysis from config.

    Reads SEM estimates from the output directory, computes effect sizes
    for configured src/des variable pairs, and generates heatmap plots.

    Parameters
    ----------
    cfg : dict
        Loaded config (from load_config).
    verbose : bool
        Print progress.
    """
    paths_cfg = cfg.get("PATHS", {})
    if not paths_cfg:
        if verbose:
            print("No PATHS section in config, skipping")
        return

    output_dir = get_output_dir(cfg)
    project_dir = get_project_dir(cfg)

    effectsize_cfg = paths_cfg.get("effectsize", {})
    if not effectsize_cfg:
        if verbose:
            print("No effectsize entries in PATHS, skipping")
        return

    # Collect effect size data from SEM output files
    pathsdata = _collect_pathsdata(output_dir, verbose)

    if not pathsdata:
        if verbose:
            print("No SEM data found in output directory")
        return

    # Save pathsdata.json
    pathsdata_path = os.path.join(project_dir, "pathsdata.json")
    with open(pathsdata_path, "w") as f:
        json.dump(pathsdata, f, indent=4)
    if verbose:
        print(f"Saved pathsdata.json ({len(pathsdata)} cases)")

    # Generate heatmaps for each destination variable
    for des_var, des_cfg in effectsize_cfg.items():
        src_vars = des_cfg.get("src", [])
        title = des_cfg.get("title", f"Effect Sizes on {des_var}")
        grid_cfg = des_cfg.get("grid", {})
        cases_filter = des_cfg.get("cases", None)

        if not src_vars:
            continue

        if verbose:
            print(f"\nGenerating heatmap: {des_var}")
            print(f"  Sources: {src_vars}")

        # Build effect size matrix
        data, case_labels, src_labels = _build_effect_matrix(
            pathsdata, des_var, src_vars, cases_filter
        )

        if data is None or data.size == 0:
            if verbose:
                print(f"  No data for {des_var}")
            continue

        # Plot if configured
        if grid_cfg.get("plot", True):
            try:
                _save_heatmap(
                    data, case_labels, src_labels,
                    title=title,
                    output_dir=output_dir,
                    plotname=grid_cfg.get("plotname", des_var),
                    grid_cfg=grid_cfg,
                )
                if verbose:
                    print(f"  Saved heatmap for {des_var}")
            except Exception as e:
                if verbose:
                    print(f"  Warning: heatmap failed: {e}")


def _collect_pathsdata(output_dir: str, verbose: bool = True) -> dict:
    """Collect effect size data from SEM estimate CSV files."""
    pathsdata = {}

    sem_files = sorted(glob.glob(os.path.join(output_dir, "*_semopy.csv")))
    for sem_file in sem_files:
        case = os.path.basename(sem_file).replace("_semopy.csv", "")
        try:
            estimates = pd.read_csv(sem_file)
            effects = {}
            for _, row in estimates.iterrows():
                if row.get("op") == "~":
                    lval = str(row.get("lval", ""))
                    rval = str(row.get("rval", ""))
                    edge_key = f"{rval} --> {lval}"
                    effects[edge_key] = {
                        "estimate": float(row.get("Estimate", 0)),
                        "pvalue": float(row.get("p-value", 1)) if "p-value" in row.index else 1.0,
                    }
            if effects:
                pathsdata[case] = effects
        except Exception as e:
            if verbose:
                print(f"  Warning: could not read {sem_file}: {e}")

    return pathsdata


def _build_effect_matrix(
    pathsdata: dict,
    des_var: str,
    src_vars: list[str],
    cases_filter: Optional[list[str]] = None,
) -> tuple[Optional[np.ndarray], list[str], list[str]]:
    """Build a cases x sources effect size matrix."""
    cases = sorted(pathsdata.keys())
    if cases_filter:
        cases = [c for c in cases if any(
            c.endswith(cf.replace(".gv", "")) or c == cf.replace(".gv", "")
            for cf in cases_filter
        )]

    if not cases:
        return None, [], []

    matrix = np.full((len(cases), len(src_vars)), np.nan)

    for i, case in enumerate(cases):
        case_effects = pathsdata.get(case, {})
        for j, src in enumerate(src_vars):
            # Try different edge formats
            for edge_key in [f"{src} --> {des_var}", f"{src} o-> {des_var}"]:
                if edge_key in case_effects:
                    matrix[i, j] = case_effects[edge_key].get("estimate", np.nan)
                    break

    return matrix, cases, src_vars


def _save_heatmap(
    data: np.ndarray,
    case_labels: list[str],
    src_labels: list[str],
    title: str,
    output_dir: str,
    plotname: str,
    grid_cfg: dict,
):
    """Save a heatmap plot of effect sizes."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    width = grid_cfg.get("widthInches", 16.0)
    height = grid_cfg.get("heightInches", max(4.0, len(case_labels) * 0.4))
    labelsize = grid_cfg.get("labelsize", 10)
    titlesize = grid_cfg.get("titleSize", 18)
    xrotate = grid_cfg.get("xrotate", 45)

    fig, ax = plt.subplots(figsize=(width, height))

    # Create DataFrame for seaborn
    df_plot = pd.DataFrame(data, index=case_labels, columns=src_labels)

    sns.heatmap(
        df_plot,
        ax=ax,
        cmap="RdBu_r",
        center=0,
        annot=True,
        fmt=".2f",
        linewidths=0.5,
        xticklabels=True,
        yticklabels=True,
    )

    ax.set_title(title, fontsize=titlesize)
    ax.tick_params(axis="x", labelsize=labelsize, rotation=xrotate)
    ax.tick_params(axis="y", labelsize=labelsize)

    plt.tight_layout()
    outpath = os.path.join(output_dir, f"{plotname}_effectsize.png")
    fig.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close(fig)
