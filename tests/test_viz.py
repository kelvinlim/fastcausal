"""Tests for fastcausal.viz — styling and graph rendering."""

import pytest

from dgraph_flex import DgraphFlex

from fastcausal.viz.styling import get_node_names, resolve_node_styles, apply_node_styles


def _make_dg(edges):
    """Create a DgraphFlex with given edge strings."""
    dg = DgraphFlex()
    for edge_str in edges:
        parts = edge_str.split(" ")
        src, edge_type, dest = parts[0], parts[1], parts[2]
        dg.graph["GRAPH"]["edges"][edge_str] = {
            "source": src,
            "target": dest,
            "edge_type": edge_type,
        }
    return dg


class TestGetNodeNames:
    def test_basic(self):
        dg = _make_dg(["X --> Y", "Y --> Z"])
        names = get_node_names(dg)
        assert names == ["X", "Y", "Z"]

    def test_deduplication(self):
        dg = _make_dg(["X --> Y", "Y --> X"])
        names = get_node_names(dg)
        assert names == ["X", "Y"]


class TestResolveNodeStyles:
    def test_exact_match(self):
        styles = [{"pattern": "X", "fillcolor": "red"}]
        resolved = resolve_node_styles(["X", "Y"], styles)
        assert "X" in resolved
        assert resolved["X"]["fillcolor"] == "red"
        assert "Y" not in resolved

    def test_wildcard_match(self):
        styles = [{"pattern": "*_lag", "shape": "box"}]
        resolved = resolve_node_styles(["X_lag", "Y_lag", "Z"], styles)
        assert "X_lag" in resolved
        assert "Y_lag" in resolved
        assert "Z" not in resolved

    def test_later_rules_override(self):
        styles = [
            {"pattern": "*", "fillcolor": "white"},
            {"pattern": "X*", "fillcolor": "blue"},
        ]
        resolved = resolve_node_styles(["X_lag", "Y"], styles)
        assert resolved["X_lag"]["fillcolor"] == "blue"
        assert resolved["Y"]["fillcolor"] == "white"

    def test_multiple_attributes(self):
        styles = [{"pattern": "*", "shape": "box", "fillcolor": "yellow", "style": "filled"}]
        resolved = resolve_node_styles(["A"], styles)
        assert resolved["A"]["shape"] == "box"
        assert resolved["A"]["fillcolor"] == "yellow"
        assert resolved["A"]["style"] == "filled"

    def test_empty_styles(self):
        resolved = resolve_node_styles(["X", "Y"], [])
        assert resolved == {}

    def test_no_matching_pattern(self):
        styles = [{"pattern": "Z*", "fillcolor": "red"}]
        resolved = resolve_node_styles(["X", "Y"], styles)
        assert resolved == {}


class TestApplyNodeStyles:
    def test_apply_styles(self):
        """Test that apply_node_styles doesn't raise errors."""
        dg = _make_dg(["X --> Y"])
        dg.load_graph()
        styles = [{"pattern": "*", "fillcolor": "lightblue", "style": "filled"}]
        apply_node_styles(dg, styles)
        # Check that dot source contains the style
        source = dg.dot.source
        assert "lightblue" in source


class TestGraphRendering:
    def test_show_graph(self):
        from fastcausal.viz.graphs import show_graph
        dg = _make_dg(["X --> Y", "Y --> Z"])
        dot = show_graph(dg)
        assert dot is not None

    def test_save_graph(self, tmp_path):
        import os
        from fastcausal.viz.graphs import save_graph
        dg = _make_dg(["X --> Y", "Y --> Z"])
        out_path = str(tmp_path / "test_graph")
        save_graph(dg, out_path, plot_format="png")
        assert os.path.exists(f"{out_path}.png")

    def test_show_graph_directed_only(self):
        from fastcausal.viz.graphs import show_graph
        dg = _make_dg(["X --> Y", "A o-o B"])
        dot = show_graph(dg, directed_only=True)
        assert dot is not None

    def test_show_graph_with_styles(self):
        from fastcausal.viz.graphs import show_graph
        dg = _make_dg(["X --> Y"])
        styles = [{"pattern": "X", "shape": "box"}]
        dot = show_graph(dg, node_styles=styles)
        assert "box" in dot.source
