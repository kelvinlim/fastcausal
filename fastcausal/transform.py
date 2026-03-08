"""
Data transformation utilities for causal discovery.

Consolidated from fastcda and tetrad-port.
"""

from typing import Optional

import numpy as np
import pandas as pd


def add_lag_columns(
    df: pd.DataFrame,
    columns: Optional[list[str]] = None,
    n_lags: int = 1,
    lag_stub: str = "_lag",
) -> pd.DataFrame:
    """
    Add lagged columns to a DataFrame for time-series causal analysis.

    Parameters
    ----------
    df : pd.DataFrame
        Time-series data (rows are time points).
    columns : list of str or None
        Columns to lag. If None, lag all numeric columns.
    n_lags : int
        Number of lags to add (default 1).
    lag_stub : str
        Suffix appended to lagged column names.

    Returns
    -------
    pd.DataFrame
        DataFrame with lagged columns appended, NaN rows dropped.
    """
    result = df.copy()
    cols = (
        columns
        if columns is not None
        else list(df.select_dtypes(include=[np.number]).columns)
    )

    for lag in range(1, n_lags + 1):
        suffix = lag_stub if n_lags == 1 else f"{lag_stub}{lag}"
        for col in cols:
            result[f"{col}{suffix}"] = df[col].shift(lag)

    return result.dropna().reset_index(drop=True)


def standardize_df_cols(
    df: pd.DataFrame,
    columns: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    Standardize columns to zero mean and unit variance.

    Parameters
    ----------
    df : pd.DataFrame
        Input data.
    columns : list of str or None
        Columns to standardize. If None, standardize all numeric columns.

    Returns
    -------
    pd.DataFrame
        Copy with specified columns standardized.
    """
    result = df.copy()
    cols = (
        columns
        if columns is not None
        else list(df.select_dtypes(include=[np.number]).columns)
    )

    for col in cols:
        mean = result[col].mean()
        std = result[col].std()
        if std > 0:
            result[col] = (result[col] - mean) / std
        else:
            result[col] = 0.0

    return result


def subsample_df(
    df: pd.DataFrame,
    fraction: float = 0.9,
) -> pd.DataFrame:
    """
    Randomly subsample rows from a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input data.
    fraction : float
        Fraction of rows to keep (0.0 to 1.0).

    Returns
    -------
    pd.DataFrame
        Subsampled DataFrame with reset index.
    """
    return df.sample(frac=fraction).reset_index(drop=True)


def add_jitter(
    df: pd.DataFrame,
    scale: float = 0.0001,
) -> pd.DataFrame:
    """
    Add small random noise to numeric columns to avoid singularity.

    Parameters
    ----------
    df : pd.DataFrame
        Input data.
    scale : float
        Standard deviation of the Gaussian noise.

    Returns
    -------
    pd.DataFrame
        Copy with jitter added to all numeric columns.
    """
    result = df.copy()
    numeric_cols = result.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        result[col] = result[col] + np.random.normal(0, scale, size=len(result))
    return result


def create_permuted_dfs(
    df: pd.DataFrame,
    n: int = 100,
) -> list[pd.DataFrame]:
    """
    Generate column-wise permuted DataFrames (for null distribution testing).

    Each permuted DataFrame has the same columns but with values
    independently shuffled within each column, destroying all
    inter-variable relationships.

    Parameters
    ----------
    df : pd.DataFrame
        Input data.
    n : int
        Number of permuted DataFrames to generate.

    Returns
    -------
    list of pd.DataFrame
        Permuted DataFrames.
    """
    permuted = []
    for _ in range(n):
        perm_df = df.copy()
        for col in perm_df.columns:
            perm_df[col] = np.random.permutation(perm_df[col].values)
        permuted.append(perm_df)
    return permuted
