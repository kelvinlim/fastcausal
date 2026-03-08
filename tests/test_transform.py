"""Tests for fastcausal.transform — pure Python, no external dependencies."""

import numpy as np
import pandas as pd
import pytest

from fastcausal.transform import (
    add_lag_columns,
    standardize_df_cols,
    subsample_df,
    add_jitter,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "A": [1.0, 2.0, 3.0, 4.0, 5.0],
        "B": [10.0, 20.0, 30.0, 40.0, 50.0],
    })


class TestAddLagColumns:
    def test_basic_lag(self, sample_df):
        result = add_lag_columns(sample_df)
        assert "A_lag" in result.columns
        assert "B_lag" in result.columns
        # One row dropped due to NaN from shift
        assert len(result) == 4

    def test_specific_columns(self, sample_df):
        result = add_lag_columns(sample_df, columns=["A"])
        assert "A_lag" in result.columns
        assert "B_lag" not in result.columns

    def test_custom_stub(self, sample_df):
        result = add_lag_columns(sample_df, lag_stub="_prev")
        assert "A_prev" in result.columns

    def test_multiple_lags(self, sample_df):
        result = add_lag_columns(sample_df, n_lags=2)
        assert "A_lag1" in result.columns
        assert "A_lag2" in result.columns
        assert len(result) == 3  # Two rows dropped


class TestStandardize:
    def test_basic_standardization(self, sample_df):
        result = standardize_df_cols(sample_df)
        assert abs(result["A"].mean()) < 1e-10
        assert abs(result["A"].std(ddof=1) - 1.0) < 1e-10

    def test_specific_columns(self, sample_df):
        result = standardize_df_cols(sample_df, columns=["A"])
        assert abs(result["A"].mean()) < 1e-10
        # B should be unchanged
        assert result["B"].tolist() == sample_df["B"].tolist()

    def test_zero_variance_column(self):
        df = pd.DataFrame({"A": [5.0, 5.0, 5.0], "B": [1.0, 2.0, 3.0]})
        result = standardize_df_cols(df)
        assert all(result["A"] == 0.0)


class TestSubsample:
    def test_fraction(self, sample_df):
        result = subsample_df(sample_df, fraction=0.6)
        assert len(result) == 3  # 60% of 5 = 3

    def test_full_sample(self, sample_df):
        result = subsample_df(sample_df, fraction=1.0)
        assert len(result) == 5


class TestAddJitter:
    def test_jitter_changes_values(self, sample_df):
        result = add_jitter(sample_df, scale=0.01)
        # Values should be close but not identical
        assert not np.array_equal(result["A"].values, sample_df["A"].values)
        assert np.allclose(result["A"].values, sample_df["A"].values, atol=0.1)
