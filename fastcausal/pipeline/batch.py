"""
Batch causal discovery across cases.

Iterates over CSV files in the data directory, runs causal discovery
and SEM on each, and saves results to the output directory.
"""

import glob
import os
import sys
from typing import Optional

import numpy as np
import pandas as pd

from fastcausal.pipeline.config import (
    get_data_dir,
    get_output_dir,
    get_causal_params,
    get_sem_params,
    get_project_dir,
)


def run_batch(
    cfg: dict,
    start: int = 0,
    end: int = -1,
    list_cases: bool = False,
    verbose: bool = True,
):
    """
    Run batch causal discovery across all cases in a project.

    Parameters
    ----------
    cfg : dict
        Loaded config (from load_config).
    start : int
        Start index for case processing.
    end : int
        End index (-1 = all cases).
    list_cases : bool
        If True, just list cases and return.
    verbose : bool
        Print progress.
    """
    from fastcausal.search import run_algorithm
    from fastcausal.knowledge import dict_to_knowledge, read_prior_file
    from fastcausal.sem import edges_to_lavaan, run_semopy
    from fastcausal.transform import standardize_df_cols, add_jitter
    from fastcausal.edges import build_dgraph
    from fastcausal.viz.graphs import save_graph

    data_dir = get_data_dir(cfg)
    output_dir = get_output_dir(cfg)
    project_dir = get_project_dir(cfg)
    params = get_causal_params(cfg)
    sem_params = get_sem_params(cfg)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Get sorted list of CSV files
    files = sorted(glob.glob(os.path.join(data_dir, "*.csv")))

    if list_cases:
        for i, f in enumerate(files):
            print(f"{i}/{len(files)}: {os.path.basename(f)}")
        return

    # Load cases to ignore
    cases_ignore = cfg.get("GLOBAL", {}).get("cases_ignore", [])

    # Load knowledge if specified
    knowledge_dict = None
    knowledge_file = params.get("knowledge")
    if knowledge_file:
        knowledge_path = os.path.join(project_dir, knowledge_file)
        if os.path.exists(knowledge_path):
            knowledge_dict = read_prior_file(knowledge_path)

    # Determine slice
    end_idx = end if end != -1 else len(files)

    for file in files[start:end_idx]:
        case = os.path.splitext(os.path.basename(file))[0]

        if case in cases_ignore:
            if verbose:
                print(f"### Ignoring case {case}")
            continue

        if verbose:
            print(f"###### fastcausal run: {case}")

        try:
            df = pd.read_csv(file)

            # Apply jitter if configured
            if params["jitter"] > 0:
                df = add_jitter(df, scale=params["jitter"])

            # Standardize if configured
            if params["standardize_cols"]:
                df = standardize_df_cols(df)

            # Build algorithm kwargs
            algo_kwargs = {"alpha": params["alpha"]}
            if params["algorithm"] in ("fges", "gfci"):
                algo_kwargs["penalty_discount"] = params["penalty_discount"]
            if params["algorithm"] in ("pc", "gfci"):
                if params["depth"] != -1:
                    algo_kwargs["depth"] = params["depth"]

            # Run search
            results, graph_info = run_algorithm(
                df,
                algorithm=params["algorithm"],
                knowledge=knowledge_dict,
                **algo_kwargs,
            )

            edges = results["edges"]

            # Save edges to text file
            edges_path = os.path.join(output_dir, f"{case}.txt")
            with open(edges_path, "w") as f:
                f.write(f"Graph Edges:\n")
                for i, edge in enumerate(edges, 1):
                    f.write(f"{i}. {edge}\n")

            # Generate and save SEM model
            if edges:
                lavaan_model = edges_to_lavaan(edges, include_types=sem_params["include_types"])

                if lavaan_model.strip():
                    # Save lavaan model
                    model_path = os.path.join(output_dir, f"{case}.lav")
                    with open(model_path, "w") as f:
                        f.write(lavaan_model)

                    # Run SEM
                    sem_results = run_semopy(lavaan_model, df)

                    if sem_results and sem_results.get("estimates") is not None:
                        # Save SEM estimates
                        estimates_path = os.path.join(output_dir, f"{case}_semopy.csv")
                        sem_results["estimates"].to_csv(estimates_path, index=False)

                        # Save fit stats
                        if sem_results.get("fit_stats"):
                            fit_path = os.path.join(output_dir, f"{case}_semopyfit.text")
                            with open(fit_path, "w") as f:
                                f.write(str(sem_results["fit_stats"]))

                    # Build and save graph
                    dg = build_dgraph(edges)
                    if sem_results and sem_results.get("estimates") is not None:
                        from fastcausal.sem import add_sem_results_to_graph
                        add_sem_results_to_graph(dg, sem_results["estimates"])

                    graph_path = os.path.join(output_dir, case)
                    try:
                        save_graph(dg, graph_path, plot_format="png", res=300)
                    except Exception as e:
                        if verbose:
                            print(f"  Warning: graph save failed: {e}")

            if verbose:
                print(f"  Edges: {len(edges)}")

        except Exception as e:
            print(f"  ERROR processing {case}: {e}")
            continue
