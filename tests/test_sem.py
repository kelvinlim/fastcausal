"""Tests for fastcausal.sem — lavaan conversion (pure Python)."""

from fastcausal.sem import edges_to_lavaan


class TestEdgesToLavaan:
    def test_directed_edges(self):
        edges = ["X --> Y", "Z --> Y"]
        model = edges_to_lavaan(edges)
        assert "Y ~ X + Z" in model

    def test_bidirected_covariance(self):
        edges = ["X <-> Y"]
        model = edges_to_lavaan(edges)
        assert "X ~~ Y" in model

    def test_o_arrow_included_by_default(self):
        edges = ["X o-> Y"]
        model = edges_to_lavaan(edges)
        assert "Y ~ X" in model

    def test_custom_include_types(self):
        edges = ["X --> Y", "A o-> B"]
        model = edges_to_lavaan(edges, include_types=["-->"])
        assert "Y ~ X" in model
        assert "B" not in model

    def test_empty_edges(self):
        assert edges_to_lavaan([]) == ""

    def test_undirected_as_covariance(self):
        edges = ["X --- Y"]
        model = edges_to_lavaan(edges)
        assert "X ~~ Y" in model
