"""
Data loading utilities and bundled sample datasets.
"""

from importlib.resources import files as pkg_resources_files

import pandas as pd


SAMPLE_DATASETS = {
    "boston": "boston_data_raw.csv",
}


def load_sample(name: str = "boston") -> pd.DataFrame:
    """
    Load a bundled sample dataset.

    Parameters
    ----------
    name : str
        Dataset name. Currently available: "boston".

    Returns
    -------
    pd.DataFrame
    """
    if name not in SAMPLE_DATASETS:
        available = ", ".join(sorted(SAMPLE_DATASETS.keys()))
        raise ValueError(f"Unknown sample dataset: {name!r}. Available: {available}")

    filename = SAMPLE_DATASETS[name]
    resource = pkg_resources_files("fastcausal.data").joinpath(filename)
    return pd.read_csv(str(resource))


def load_csv(path: str) -> pd.DataFrame:
    """
    Load a CSV file as a DataFrame.

    Parameters
    ----------
    path : str
        Path to the CSV file.

    Returns
    -------
    pd.DataFrame
    """
    return pd.read_csv(path)
