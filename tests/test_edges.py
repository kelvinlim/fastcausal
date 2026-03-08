"""Tests for fastcausal.edges — pure Python, no external dependencies."""

import pytest

from fastcausal.edges import extract_edges, select_edges, parse_edges_to_graph_info


class TestExtractEdges:
    def test_basic_extraction(self):
        text = """Graph Edges:
1. X --> Y
2. A o-> B
3. C o-o D
"""
        edges = extract_edges(text)
        assert edges == ["X --> Y", "A o-> B", "C o-o D"]

    def test_empty_input(self):
        assert extract_edges("") == []

    def test_no_edges(self):
        assert extract_edges("Some random text\nwithout edges") == []

    def test_various_edge_types(self):
        text = "1. A --> B\n2. C <-> D\n3. E --- F\n4. G o-o H\n"
        edges = extract_edges(text)
        assert len(edges) == 4


class TestSelectEdges:
    def test_basic_selection(self):
        counts = {"X --> Y": 0.9, "A o-> B": 0.5, "C o-o D": 0.8}
        selected = select_edges(counts, min_fraction=0.75)
        assert "X --> Y" in selected
        assert "C o-o D" in selected
        assert "A o-> B" not in selected

    def test_all_above_threshold(self):
        counts = {"X --> Y": 1.0, "A --> B": 0.95}
        selected = select_edges(counts, min_fraction=0.5)
        assert len(selected) == 2


class TestParseEdgesToGraphInfo:
    def test_directed(self):
        info = parse_edges_to_graph_info(["X --> Y"], ["X", "Y"])
        assert ("X", "Y") in info["directed_edges"]

    def test_bidirected(self):
        info = parse_edges_to_graph_info(["X <-> Y"], ["X", "Y"])
        assert ("X", "Y") in info["bidirected_edges"]

    def test_adjacency(self):
        info = parse_edges_to_graph_info(["X --> Y"], ["X", "Y"])
        assert "Y" in info["adjacency"]["X"]
        assert "X" in info["adjacency"]["Y"]
