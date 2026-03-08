"""
Data preparation engine.

Ported from cda_tools2's run_parse2.py (ParseData4 class).
Provides a config-driven pipeline for processing raw data into
per-case CSV files ready for causal discovery.
"""

import os
import sys

import numpy as np
import pandas as pd

from fastcausal.pipeline.config import (
    get_project_dir,
    get_data_dir,
    get_raw_data_dir,
)


def run_parse(cfg: dict, verbose: bool = True):
    """
    Run data preparation pipeline from a config.

    Reads source data, applies global steps, splits by case ID,
    applies per-case steps, saves processed files, and generates
    a prior knowledge file.

    Parameters
    ----------
    cfg : dict
        Loaded config (from load_config).
    verbose : bool
        Print progress.
    """
    project_dir = get_project_dir(cfg)
    data_dir = get_data_dir(cfg)
    raw_dir = get_raw_data_dir(cfg)
    prep = cfg.get("PREP", {})

    # Create directories
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(raw_dir, exist_ok=True)

    # Read source data
    datafile = prep.get("datafile", "")
    if not os.path.isabs(datafile):
        datafile = os.path.join(project_dir, datafile)

    if not os.path.exists(datafile):
        raise FileNotFoundError(f"Source data file not found: {datafile}")

    if verbose:
        print(f"Reading: {datafile}")
    df = pd.read_csv(datafile)
    if verbose:
        print(f"  Shape: {df.shape}")

    # Apply global steps
    steps_global = prep.get("steps_global", [])
    df = _run_steps("global", df, steps_global, project_dir, verbose)

    # Track variable list from processed global data
    varlist = list(df.columns)

    # Check for per-case processing
    steps_case = prep.get("steps_case", [])
    if not steps_case:
        if verbose:
            print("No steps_case defined, skipping per-case processing")
        return

    # Get minimum row thresholds
    variables = prep.get("variables", {})
    min_rows = variables.get("min_rows", 40)
    min_raw_rows = variables.get("min_raw_rows", 20)

    # Split by 'id' column
    if "id" not in df.columns:
        raise ValueError("DataFrame must have an 'id' column for per-case processing")

    cases = sorted(df["id"].unique())
    cases_ignore = cfg.get("GLOBAL", {}).get("cases_ignore", [])

    all_cases_frames = []
    case_summaries = []

    for case in cases:
        # Create label
        if isinstance(case, str):
            label = case
        elif isinstance(case, (int, np.integer)):
            label = f"sub_{case:05d}"
        elif isinstance(case, float):
            label = f"sub_{int(case):05d}"
        else:
            label = str(case)

        df_case = df[df["id"] == case].copy()
        summ = {"id": label, "len_orig": len(df_case)}

        if verbose:
            print(f"\n{label} ({len(df_case)} rows)")

        if len(df_case) < min_raw_rows:
            if verbose:
                print(f"  Skipping: only {len(df_case)} rows (min: {min_raw_rows})")
            summ["len_clean"] = 0
            case_summaries.append(summ)
            continue

        # Apply per-case steps
        df_processed = _run_steps(label, df_case, steps_case, project_dir, verbose)
        summ["len_clean"] = len(df_processed)

        # Accumulate for all_cases if meets threshold and not ignored
        if len(df_processed) >= min_rows and case not in cases_ignore:
            all_cases_frames.append(df_processed)

        case_summaries.append(summ)

    # Write all_cases.csv
    if all_cases_frames:
        all_cases = pd.concat(all_cases_frames, ignore_index=True)
        all_cases_path = os.path.join(data_dir, "all_cases.csv")
        all_cases.to_csv(all_cases_path, index=False)
        if verbose:
            print(f"\nall_cases.csv: {all_cases.shape}")

        # Create prior file from variable list
        varlist = list(all_cases.columns)
        _create_prior_file(varlist, project_dir, cfg)
    else:
        print("Warning: no data in all_cases")

    # Write case summary
    summ_df = pd.DataFrame(case_summaries)
    summ_path = os.path.join(project_dir, "case_details.csv")
    summ_df.to_csv(summ_path, index=False)
    if verbose:
        print(f"\nCase details saved to {summ_path}")


def _run_steps(
    label: str,
    df: pd.DataFrame,
    steps: list[dict],
    project_dir: str,
    verbose: bool = True,
) -> pd.DataFrame:
    """Execute a list of processing steps on a DataFrame."""
    for step in steps:
        op = step.get("op", "")
        arg = step.get("arg")

        if verbose:
            print(f"  op: {op}")

        if op == "sort":
            df = df.sort_values(by=arg).reset_index(drop=True)
        elif op == "keep":
            cols = [c for c in arg if c in df.columns]
            df = df[cols]
        elif op == "drop":
            cols = [c for c in arg if c in df.columns]
            df = df.drop(columns=cols)
        elif op == "rename":
            if isinstance(arg, dict):
                df = df.rename(columns=arg)
        elif op == "recode":
            df = _step_recode(df, arg)
        elif op == "replace_values":
            df = _step_replace_values(df, arg)
        elif op == "missing_value":
            if arg == "drop":
                df = df.dropna().reset_index(drop=True)
            elif arg == "pad":
                df = df.ffill()
        elif op == "missing_value_columns":
            if isinstance(arg, dict):
                for col, val in arg.items():
                    if col in df.columns:
                        df[col] = df[col].fillna(val)
        elif op == "add_lag":
            from fastcausal.transform import add_lag_columns
            df = add_lag_columns(df)
        elif op == "standardize":
            from fastcausal.transform import standardize_df_cols
            df = standardize_df_cols(df)
        elif op == "save":
            if isinstance(arg, dict):
                save_dir = arg.get("dir", "data")
                stub = arg.get("stub", ".csv")
                min_save_rows = arg.get("min_rows", 0)

                if len(df) >= min_save_rows:
                    save_path = os.path.join(project_dir, save_dir)
                    os.makedirs(save_path, exist_ok=True)
                    filepath = os.path.join(save_path, f"{label}{stub}")
                    df.to_csv(filepath, index=False)
                    if verbose:
                        print(f"    Saved: {filepath} ({len(df)} rows)")
                else:
                    if verbose:
                        print(f"    Skipped save: {len(df)} < {min_save_rows} rows")
        elif op == "query":
            if isinstance(arg, str):
                df = df.query(arg).reset_index(drop=True)
        elif op == "reverse":
            if isinstance(arg, dict):
                for col, max_val in arg.items():
                    if col in df.columns:
                        df[col] = max_val - df[col]
        elif op == "max_columns":
            if isinstance(arg, dict):
                new_col = arg.get("name", "max_col")
                cols = arg.get("columns", [])
                existing = [c for c in cols if c in df.columns]
                if existing:
                    df[new_col] = df[existing].max(axis=1)
        elif op == "mean_columns":
            if isinstance(arg, dict):
                new_col = arg.get("name", "mean_col")
                cols = arg.get("columns", [])
                existing = [c for c in cols if c in df.columns]
                if existing:
                    df[new_col] = df[existing].mean(axis=1)
        elif op == "sum_columns":
            if isinstance(arg, dict):
                new_col = arg.get("name", "sum_col")
                cols = arg.get("columns", [])
                existing = [c for c in cols if c in df.columns]
                if existing:
                    df[new_col] = df[existing].sum(axis=1)
        elif op == "droprows":
            if isinstance(arg, dict):
                for col, vals in arg.items():
                    if col in df.columns:
                        df = df[~df[col].isin(vals)].reset_index(drop=True)
        elif op == "keeprows":
            if isinstance(arg, dict):
                for col, vals in arg.items():
                    if col in df.columns:
                        df = df[df[col].isin(vals)].reset_index(drop=True)
        else:
            if verbose:
                print(f"    Warning: unknown operation '{op}', skipping")

    return df


def _step_recode(df: pd.DataFrame, arg: dict) -> pd.DataFrame:
    """Recode values in columns based on a mapping dict."""
    if not isinstance(arg, dict):
        return df
    for col, mapping in arg.items():
        if col in df.columns:
            df[col] = df[col].map(
                lambda x, m=mapping: m.get(str(x), m.get(x, x))
            )
            # Attempt float conversion
            try:
                df[col] = df[col].astype(float)
            except (ValueError, TypeError):
                pass
    return df


def _step_replace_values(df: pd.DataFrame, arg: dict) -> pd.DataFrame:
    """Replace specific values, leaving unmapped values unchanged."""
    if not isinstance(arg, dict):
        return df
    for col, mapping in arg.items():
        if col in df.columns:
            df[col] = df[col].replace(mapping)
    return df


def _create_prior_file(varlist: list[str], project_dir: str, cfg: dict):
    """Create a prior.txt file from the variable list."""
    prep = cfg.get("PREP", {})
    overwrite = prep.get("overwrite_prior", True)
    prior_path = os.path.join(project_dir, "prior.txt")

    if os.path.exists(prior_path) and not overwrite:
        return

    # Separate lag and current variables
    lag_vars = [v for v in varlist if "_lag" in v]
    current_vars = [v for v in varlist if "_lag" not in v]

    with open(prior_path, "w") as f:
        f.write("/knowledge\n")
        f.write("addtemporal\n")
        if lag_vars:
            f.write(f"0 {' '.join(lag_vars)}\n")
        f.write(f"1 {' '.join(current_vars)}\n")
