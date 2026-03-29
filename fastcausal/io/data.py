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

        The "boston" dataset contains daily EMA (Ecological Momentary
        Assessment) measurements (alcohol use, sleep, mood) from:

        Lim KO et al. "Ecological momentary assessment of alcohol use and
        related constructs in veterans with PTSD." *J Dual Diagn.* 2021.
        https://pubmed.ncbi.nlm.nih.gov/33863920/

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
