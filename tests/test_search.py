"""Integration tests for fastcausal.search — requires tetrad-port C++ extension."""

import pytest
import numpy as np
import pandas as pd

from fastcausal.search import run_algorithm


@pytest.fixture
def sample_df():
    """Create a small DataFrame with a clear causal structure: X -> Y -> Z."""
    np.random.seed(42)
    n = 200
    X = np.random.randn(n)
    Y = 0.8 * X + 0.2 * np.random.randn(n)
    Z = 0.6 * Y + 0.3 * np.random.randn(n)
    return pd.DataFrame({"X": X, "Y": Y, "Z": Z})


class TestRunAlgorithm:
    def test_gfci_returns_results(self, sample_df):
        results, graph_info = run_algorithm(sample_df, algorithm="gfci")
        assert "edges" in results
        assert isinstance(results["edges"], list)

    def test_pc_returns_results(self, sample_df):
        results, graph_info = run_algorithm(sample_df, algorithm="pc")
        assert "edges" in results

    def test_fges_returns_results(self, sample_df):
        results, graph_info = run_algorithm(sample_df, algorithm="fges")
        assert "edges" in results

    def test_finds_edges(self, sample_df):
        """With clear causal structure, algorithm should find at least one edge."""
        results, _ = run_algorithm(sample_df, algorithm="fges")
        assert len(results["edges"]) > 0

    def test_invalid_algorithm(self, sample_df):
        with pytest.raises(ValueError, match="Unknown algorithm"):
            run_algorithm(sample_df, algorithm="invalid")

    def test_with_knowledge(self, sample_df):
        knowledge = {"addtemporal": {0: ["X"], 1: ["Y", "Z"]}}
        results, _ = run_algorithm(sample_df, algorithm="gfci", knowledge=knowledge)
        assert "edges" in results

    def test_alpha_parameter(self, sample_df):
        results_strict, _ = run_algorithm(sample_df, algorithm="pc", alpha=0.001)
        results_loose, _ = run_algorithm(sample_df, algorithm="pc", alpha=0.1)
        # Stricter alpha should find same or fewer edges
        assert len(results_strict["edges"]) <= len(results_loose["edges"])

    def test_penalty_discount(self, sample_df):
        results, _ = run_algorithm(
            sample_df, algorithm="fges", penalty_discount=2.0
        )
        assert "edges" in results
