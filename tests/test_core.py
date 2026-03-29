"""Integration tests for FastCausal class — end-to-end workflows."""

import os
import tempfile

import pytest
import numpy as np
import pandas as pd

from fastcausal import FastCausal


@pytest.fixture
def fc():
    return FastCausal(verbose=0)


@pytest.fixture
def sample_df():
    np.random.seed(42)
    n = 200
    X = np.random.randn(n)
    Y = 0.8 * X + 0.2 * np.random.randn(n)
    Z = 0.6 * Y + 0.3 * np.random.randn(n)
    return pd.DataFrame({"X": X, "Y": Y, "Z": Z})


class TestDataLoading:
    def test_load_sample(self, fc):
        df = fc.load_sample("boston")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_load_csv(self, fc, sample_df, tmp_path):
        csv_path = tmp_path / "test.csv"
        sample_df.to_csv(csv_path, index=False)
        df = fc.load_csv(str(csv_path))
        assert df.shape == sample_df.shape


class TestTransformations:
    def test_add_lag(self, fc, sample_df):
        result = fc.add_lag_columns(sample_df)
        assert any("_lag" in c for c in result.columns)

    def test_standardize(self, fc, sample_df):
        result = fc.standardize(sample_df)
        assert abs(result["X"].mean()) < 0.01
        assert abs(result["X"].std() - 1.0) < 0.1

    def test_subsample(self, fc, sample_df):
        result = fc.subsample(sample_df, fraction=0.5)
        assert len(result) < len(sample_df)


class TestKnowledge:
    def test_create_lag_knowledge(self, fc):
        k = fc.create_lag_knowledge(["X", "Y"])
        assert k["addtemporal"][0] == ["X_lag", "Y_lag"]
        assert k["addtemporal"][1] == ["X", "Y"]


class TestSearch:
    def test_run_search_no_sem(self, fc, sample_df):
        results, dg = fc.run_search(sample_df, algorithm="fges", run_sem=False)
        assert "edges" in results
        assert len(results["edges"]) > 0
        assert dg is not None

    def test_run_search_with_sem(self, fc, sample_df):
        results, dg = fc.run_search(
            sample_df, algorithm="fges", run_sem=True
        )
        assert "edges" in results
        # SEM only runs when directed edges (-->, o->) are present;
        # undirected (---) and bidirected (<->) edges are excluded from the
        # lavaan model by default since they represent latent confounding.
        has_directed = any(
            "-->" in e or "o->" in e for e in results["edges"]
        )
        if has_directed:
            assert "sem_results" in results

    def test_run_search_with_knowledge(self, fc, sample_df):
        knowledge = {"addtemporal": {0: ["X"], 1: ["Y", "Z"]}}
        results, dg = fc.run_search(
            sample_df, algorithm="gfci", knowledge=knowledge, run_sem=False
        )
        assert "edges" in results


class TestEndToEnd:
    def test_full_workflow(self, fc):
        """Test the complete interactive workflow."""
        df = fc.load_sample("boston")
        # Use a subset of columns for speed
        cols = list(df.columns[:4])
        df_sub = df[cols].dropna()

        results, dg = fc.run_search(
            df_sub, algorithm="fges", run_sem=False
        )
        assert "edges" in results

    def test_save_graph(self, fc, sample_df, tmp_path):
        """Test graph saving."""
        results, dg = fc.run_search(
            sample_df, algorithm="fges", run_sem=False
        )
        if results["edges"]:
            out_path = str(tmp_path / "test_graph")
            fc.save_graph(dg, out_path, plot_format="png")
            assert os.path.exists(f"{out_path}.png")
