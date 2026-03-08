"""
YAML config parsing for batch processing pipeline.

Supports v5.0 (new) and v4.0 (legacy with deprecation warning) formats.
"""

import os
import warnings
from typing import Any

import yaml


def load_config(config_path: str) -> dict[str, Any]:
    """
    Load and validate a project config.yaml file.

    Supports v5.0 (current) and v4.0 (legacy) formats.
    v4.0 configs emit a deprecation warning and have their
    CAUSAL section automatically mapped to the v5.0 format.

    Parameters
    ----------
    config_path : str
        Path to config.yaml file.

    Returns
    -------
    dict
        Parsed and normalized config dictionary.
    """
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    # Determine project directory from config path
    cfg["_project_dir"] = os.path.dirname(os.path.abspath(config_path))
    cfg["_config_path"] = os.path.abspath(config_path)

    version = cfg.get("GLOBAL", {}).get("version", 4.0)

    if float(version) < 5.0:
        warnings.warn(
            f"Config version {version} is deprecated. "
            "Please update to version 5.0. See migration guide at "
            "https://github.com/kelvinlim/fastcausal/docs/migration_from_cda_tools2.md",
            DeprecationWarning,
            stacklevel=2,
        )
        cfg = _migrate_v4_to_v5(cfg)

    _validate_config(cfg)
    return cfg


def _migrate_v4_to_v5(cfg: dict) -> dict:
    """
    Migrate a v4.0 config to v5.0 format.

    Extracts algorithm parameters from the nested causal-cmd sub-key
    and flattens them into the CAUSAL section.
    """
    causal = cfg.get("CAUSAL", {})

    # Extract from causal-cmd sub-key if present
    causal_cmd = causal.get("causal-cmd", {})
    if causal_cmd:
        # Map v4.0 causal-cmd fields to v5.0 flat fields
        if "algorithm" not in causal and "algorithm" in causal_cmd:
            causal["algorithm"] = causal_cmd["algorithm"]
        if "alpha" not in causal and "alpha" in causal_cmd:
            causal["alpha"] = causal_cmd["alpha"]
        if "penaltyDiscount" in causal_cmd and "penalty_discount" not in causal:
            causal["penalty_discount"] = causal_cmd["penaltyDiscount"]
        if "knowledge" not in causal and "knowledge" in causal_cmd:
            causal["knowledge"] = causal_cmd["knowledge"]
        if "out" not in causal and "out" in causal_cmd:
            causal["out"] = causal_cmd["out"]

    # Also check for fastcda sub-key (from run_causal3.py configs)
    fastcda_cfg = causal.get("fastcda", {})
    if fastcda_cfg:
        if "algorithm" not in causal and "algorithm" in fastcda_cfg:
            causal["algorithm"] = fastcda_cfg["algorithm"]
        if "out" not in causal and "out" in fastcda_cfg:
            causal["out"] = fastcda_cfg["out"]

    cfg["CAUSAL"] = causal
    return cfg


def _validate_config(cfg: dict) -> None:
    """Basic config validation."""
    if "GLOBAL" not in cfg:
        raise ValueError("Config must have a GLOBAL section")


def get_project_dir(cfg: dict) -> str:
    """Get the project directory from a loaded config."""
    return cfg["_project_dir"]


def get_data_dir(cfg: dict) -> str:
    """Get the data directory path."""
    project_dir = get_project_dir(cfg)
    datadir = cfg.get("GLOBAL", {}).get("directories", {}).get("datadir", "data")
    return os.path.join(project_dir, datadir)


def get_output_dir(cfg: dict) -> str:
    """Get the output directory path."""
    project_dir = get_project_dir(cfg)
    # Check CAUSAL.out first, then GLOBAL.directories.output
    output = cfg.get("CAUSAL", {}).get("out")
    if not output:
        output = cfg.get("GLOBAL", {}).get("directories", {}).get("output", "output")
    return os.path.join(project_dir, output)


def get_raw_data_dir(cfg: dict) -> str:
    """Get the raw data directory path."""
    project_dir = get_project_dir(cfg)
    rawdir = cfg.get("GLOBAL", {}).get("directories", {}).get("rawdatadir", "data_raw")
    return os.path.join(project_dir, rawdir)


def get_causal_params(cfg: dict) -> dict:
    """
    Extract causal discovery parameters from config.

    Returns
    -------
    dict with keys: algorithm, alpha, penalty_discount, knowledge, etc.
    """
    causal = cfg.get("CAUSAL", {})
    return {
        "algorithm": causal.get("algorithm", "gfci"),
        "alpha": float(causal.get("alpha", 0.05)),
        "penalty_discount": float(causal.get("penalty_discount", 1.0)),
        "depth": int(causal.get("depth", -1)),
        "max_degree": int(causal.get("max_degree", -1)),
        "knowledge": causal.get("knowledge"),
        "standardize_cols": causal.get("standardize_cols", True),
        "jitter": float(causal.get("jitter", 0.0)),
    }


def get_sem_params(cfg: dict) -> dict:
    """Extract SEM parameters from config."""
    sem = cfg.get("SEM", {})
    plotting = sem.get("plotting", {})
    include_edges = sem.get("include_model_edges", [["-->", "~"], ["o->", "~"]])
    include_types = [pair[0] for pair in include_edges if len(pair) >= 1]
    return {
        "plot_all_edges": plotting.get("plot_all_edges", False),
        "fontname": plotting.get("fontname", "Helvetica"),
        "label_edge_types": plotting.get("label_edge_types", ["-->", "o->", "o-o"]),
        "min_pvalue": plotting.get("min_pvalue", 1),
        "show_pvalue": plotting.get("show_pvalue", True),
        "label": plotting.get("label", True),
        "include_types": include_types,
    }
