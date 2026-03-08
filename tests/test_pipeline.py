"""Tests for fastcausal.pipeline — batch, parse, paths, report, metrics."""

import os

import pytest
import numpy as np
import pandas as pd

try:
    import networkx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

from fastcausal.pipeline.metrics import (
    get_parent_child_edges,
    compute_effect_sizes,
)

networkx_required = pytest.mark.skipif(
    not HAS_NETWORKX, reason="networkx not installed"
)


# ---- Metrics tests (pure Python + networkx) ----

@networkx_required
class TestCreateNetworkxGraph:
    def test_directed_edge(self):
        from fastcausal.pipeline.metrics import create_networkx_graph
        G = create_networkx_graph(["X --> Y"])
        assert G.has_edge("X", "Y")
        assert not G.has_edge("Y", "X")

    def test_o_arrow_edge(self):
        from fastcausal.pipeline.metrics import create_networkx_graph
        G = create_networkx_graph(["X o-> Y"])
        assert G.has_edge("X", "Y")

    def test_undirected_edge(self):
        from fastcausal.pipeline.metrics import create_networkx_graph
        G = create_networkx_graph(["X --- Y"])
        assert G.has_edge("X", "Y")
        assert G.has_edge("Y", "X")

    def test_bidirected_edge(self):
        from fastcausal.pipeline.metrics import create_networkx_graph
        G = create_networkx_graph(["X <-> Y"])
        assert G.has_edge("X", "Y")
        assert G.has_edge("Y", "X")

    def test_multiple_edges(self):
        from fastcausal.pipeline.metrics import create_networkx_graph
        G = create_networkx_graph(["X --> Y", "Y --> Z", "A o-> B"])
        assert G.number_of_edges() == 3

    def test_invalid_edge_skipped(self):
        from fastcausal.pipeline.metrics import create_networkx_graph
        G = create_networkx_graph(["invalid", "X --> Y"])
        assert G.number_of_edges() == 1


@networkx_required
class TestDegreeCentrality:
    def test_basic(self):
        from fastcausal.pipeline.metrics import degree_centrality
        dc = degree_centrality(["X --> Y", "Y --> Z"])
        assert "X" in dc
        assert "Y" in dc
        assert "Z" in dc
        # Y has the highest degree (2 edges: in from X, out to Z)
        assert dc["Y"] >= dc["X"]


@networkx_required
class TestGetAncestors:
    def test_direct_parent(self):
        from fastcausal.pipeline.metrics import get_ancestors
        anc = get_ancestors(["X --> Y"], ["Y"])
        assert "X" in anc["Y"]

    def test_transitive_ancestor(self):
        from fastcausal.pipeline.metrics import get_ancestors
        anc = get_ancestors(["X --> Y", "Y --> Z"], ["Z"])
        assert "X" in anc["Z"]
        assert "Y" in anc["Z"]

    def test_no_ancestors(self):
        from fastcausal.pipeline.metrics import get_ancestors
        anc = get_ancestors(["X --> Y"], ["X"])
        assert anc["X"] == []

    def test_missing_node(self):
        from fastcausal.pipeline.metrics import get_ancestors
        anc = get_ancestors(["X --> Y"], ["W"])
        assert anc["W"] == []


class TestGetParentChildEdges:
    def test_basic(self):
        edges = ["X --> Y", "Y --> Z", "A --> B"]
        result = get_parent_child_edges(edges, parents=["X", "Y"], children=["Y", "Z"])
        assert "X --> Y" in result
        assert "Y --> Z" in result
        assert "A --> B" not in result

    def test_no_match(self):
        edges = ["X --> Y"]
        result = get_parent_child_edges(edges, parents=["A"], children=["B"])
        assert result == []


class TestComputeEffectSizes:
    def test_basic(self):
        estimates = pd.DataFrame({
            "lval": ["Y", "Z"],
            "rval": ["X", "Y"],
            "op": ["~", "~"],
            "Estimate": [0.8, 0.6],
        })
        edges = ["X --> Y", "Y --> Z"]
        effects = compute_effect_sizes(estimates, edges)
        assert "X --> Y" in effects
        assert abs(effects["X --> Y"] - 0.8) < 1e-6

    def test_none_estimates(self):
        effects = compute_effect_sizes(None, ["X --> Y"])
        assert effects == {}

    def test_no_matching_edges(self):
        estimates = pd.DataFrame({
            "lval": ["B"],
            "rval": ["A"],
            "op": ["~"],
            "Estimate": [0.5],
        })
        effects = compute_effect_sizes(estimates, ["X --> Y"])
        assert effects == {}


# ---- Parse step tests (pure Python) ----

class TestParseSteps:
    def test_run_steps_sort(self):
        from fastcausal.pipeline.parse import _run_steps
        df = pd.DataFrame({"x": [3, 1, 2]})
        result = _run_steps("test", df, [{"op": "sort", "arg": "x"}], ".", verbose=False)
        assert list(result["x"]) == [1, 2, 3]

    def test_run_steps_keep(self):
        from fastcausal.pipeline.parse import _run_steps
        df = pd.DataFrame({"x": [1], "y": [2], "z": [3]})
        result = _run_steps("test", df, [{"op": "keep", "arg": ["x", "z"]}], ".", verbose=False)
        assert list(result.columns) == ["x", "z"]

    def test_run_steps_drop(self):
        from fastcausal.pipeline.parse import _run_steps
        df = pd.DataFrame({"x": [1], "y": [2], "z": [3]})
        result = _run_steps("test", df, [{"op": "drop", "arg": ["y"]}], ".", verbose=False)
        assert "y" not in result.columns

    def test_run_steps_rename(self):
        from fastcausal.pipeline.parse import _run_steps
        df = pd.DataFrame({"x": [1]})
        result = _run_steps("test", df, [{"op": "rename", "arg": {"x": "new_x"}}], ".", verbose=False)
        assert "new_x" in result.columns

    def test_run_steps_query(self):
        from fastcausal.pipeline.parse import _run_steps
        df = pd.DataFrame({"x": [1, 2, 3, 4, 5]})
        result = _run_steps("test", df, [{"op": "query", "arg": "x > 3"}], ".", verbose=False)
        assert len(result) == 2

    def test_run_steps_missing_value_drop(self):
        from fastcausal.pipeline.parse import _run_steps
        df = pd.DataFrame({"x": [1, None, 3]})
        result = _run_steps("test", df, [{"op": "missing_value", "arg": "drop"}], ".", verbose=False)
        assert len(result) == 2

    def test_run_steps_reverse(self):
        from fastcausal.pipeline.parse import _run_steps
        df = pd.DataFrame({"x": [1, 2, 3]})
        result = _run_steps("test", df, [{"op": "reverse", "arg": {"x": 4}}], ".", verbose=False)
        assert list(result["x"]) == [3, 2, 1]

    def test_run_steps_mean_columns(self):
        from fastcausal.pipeline.parse import _run_steps
        df = pd.DataFrame({"a": [2.0, 4.0], "b": [6.0, 8.0]})
        result = _run_steps(
            "test", df,
            [{"op": "mean_columns", "arg": {"name": "avg", "columns": ["a", "b"]}}],
            ".", verbose=False,
        )
        assert "avg" in result.columns
        assert abs(result["avg"].iloc[0] - 4.0) < 1e-6

    def test_run_steps_sum_columns(self):
        from fastcausal.pipeline.parse import _run_steps
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        result = _run_steps(
            "test", df,
            [{"op": "sum_columns", "arg": {"name": "total", "columns": ["a", "b"]}}],
            ".", verbose=False,
        )
        assert result["total"].iloc[0] == 4

    def test_run_steps_droprows(self):
        from fastcausal.pipeline.parse import _run_steps
        df = pd.DataFrame({"x": [1, 2, 3, 4]})
        result = _run_steps(
            "test", df,
            [{"op": "droprows", "arg": {"x": [2, 4]}}],
            ".", verbose=False,
        )
        assert list(result["x"]) == [1, 3]

    def test_run_steps_keeprows(self):
        from fastcausal.pipeline.parse import _run_steps
        df = pd.DataFrame({"x": [1, 2, 3, 4]})
        result = _run_steps(
            "test", df,
            [{"op": "keeprows", "arg": {"x": [1, 3]}}],
            ".", verbose=False,
        )
        assert list(result["x"]) == [1, 3]

    def test_run_steps_replace_values(self):
        from fastcausal.pipeline.parse import _run_steps
        df = pd.DataFrame({"x": [1, 2, 3]})
        result = _run_steps(
            "test", df,
            [{"op": "replace_values", "arg": {"x": {1: 10, 3: 30}}}],
            ".", verbose=False,
        )
        assert list(result["x"]) == [10, 2, 30]

    def test_run_steps_unknown_op_ignored(self):
        from fastcausal.pipeline.parse import _run_steps
        df = pd.DataFrame({"x": [1, 2]})
        result = _run_steps("test", df, [{"op": "nonexistent_op"}], ".", verbose=False)
        assert len(result) == 2  # unchanged


# ---- Paths/report helpers (config-dependent, tested via unit mocking) ----

class TestPathsBuildEffectMatrix:
    def test_basic_matrix(self):
        from fastcausal.pipeline.paths import _build_effect_matrix
        pathsdata = {
            "case1": {"X --> Y": {"estimate": 0.5, "pvalue": 0.01}},
            "case2": {"X --> Y": {"estimate": 0.8, "pvalue": 0.001}},
        }
        data, cases, srcs = _build_effect_matrix(pathsdata, "Y", ["X"])
        assert data.shape == (2, 1)
        assert abs(data[0, 0] - 0.5) < 1e-6
        assert abs(data[1, 0] - 0.8) < 1e-6

    def test_missing_edge(self):
        from fastcausal.pipeline.paths import _build_effect_matrix
        pathsdata = {
            "case1": {"X --> Y": {"estimate": 0.5}},
        }
        data, cases, srcs = _build_effect_matrix(pathsdata, "Y", ["X", "Z"])
        assert data.shape == (1, 2)
        assert np.isnan(data[0, 1])

    def test_cases_filter(self):
        from fastcausal.pipeline.paths import _build_effect_matrix
        pathsdata = {
            "case1": {"X --> Y": {"estimate": 0.5}},
            "case2": {"X --> Y": {"estimate": 0.8}},
        }
        data, cases, srcs = _build_effect_matrix(
            pathsdata, "Y", ["X"], cases_filter=["case1"]
        )
        assert len(cases) == 1
        assert cases[0] == "case1"

    def test_empty_pathsdata(self):
        from fastcausal.pipeline.paths import _build_effect_matrix
        data, cases, srcs = _build_effect_matrix({}, "Y", ["X"])
        assert data is None
