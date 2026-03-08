"""
FastCausal - Main user-facing API for causal discovery analysis.

This module provides the FastCausal class which is the single entry point
for interactive and programmatic causal discovery workflows.
"""

from typing import Optional

import pandas as pd

from dgraph_flex import DgraphFlex


class FastCausal:
    """
    Main class for causal discovery analysis.

    Provides a unified interface for:
    - Loading and transforming data
    - Running causal discovery algorithms (PC, FGES, GFCI)
    - Fitting structural equation models (SEM)
    - Visualizing causal graphs

    Example
    -------
    >>> fc = FastCausal()
    >>> df = fc.load_sample("boston")
    >>> results, graph = fc.run_search(df, algorithm="gfci")
    >>> fc.show_graph(graph)
    """

    def __init__(self, verbose: int = 1):
        self.verbose = verbose

    # -- Data loading --

    def load_sample(self, name: str = "boston") -> pd.DataFrame:
        """Load a bundled sample dataset."""
        from fastcausal.io.data import load_sample
        return load_sample(name)

    def load_csv(self, path: str) -> pd.DataFrame:
        """Load a CSV file as a DataFrame."""
        from fastcausal.io.data import load_csv
        return load_csv(path)

    # -- Data transformation --

    def add_lag_columns(
        self,
        df: pd.DataFrame,
        columns: Optional[list[str]] = None,
        n_lags: int = 1,
        lag_stub: str = "_lag",
    ) -> pd.DataFrame:
        """Add lagged columns to a DataFrame for time-series causal analysis."""
        from fastcausal.transform import add_lag_columns
        return add_lag_columns(df, columns=columns, n_lags=n_lags, lag_stub=lag_stub)

    def standardize(
        self,
        df: pd.DataFrame,
        columns: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """Standardize columns to zero mean and unit variance."""
        from fastcausal.transform import standardize_df_cols
        return standardize_df_cols(df, columns=columns)

    def subsample(
        self,
        df: pd.DataFrame,
        fraction: float = 0.9,
    ) -> pd.DataFrame:
        """Randomly subsample rows from a DataFrame."""
        from fastcausal.transform import subsample_df
        return subsample_df(df, fraction=fraction)

    # -- Knowledge --

    def create_lag_knowledge(
        self,
        columns: list[str],
        lag_stub: str = "_lag",
    ) -> dict:
        """Create a temporal knowledge dict for lagged data."""
        from fastcausal.knowledge import create_lag_knowledge
        return create_lag_knowledge(columns, lag_stub=lag_stub)

    # -- Search --

    def run_search(
        self,
        df: pd.DataFrame,
        algorithm: str = "gfci",
        knowledge: Optional[dict] = None,
        run_sem: bool = True,
        **kwargs,
    ) -> tuple[dict, DgraphFlex]:
        """
        Run a single causal discovery search.

        Parameters
        ----------
        df : pd.DataFrame
            Continuous numeric data.
        algorithm : str
            One of "pc", "fges", "gfci".
        knowledge : dict or None
            Prior knowledge dict (e.g. from create_lag_knowledge).
        run_sem : bool
            If True, fit a SEM and decorate the graph with results.
        **kwargs
            Additional algorithm parameters (alpha, penalty_discount, etc.)

        Returns
        -------
        results : dict
            Search results including edges, nodes, and optionally SEM results.
        graph : DgraphFlex
            Graph object for visualization.
        """
        from fastcausal.search import run_algorithm
        from fastcausal.edges import build_dgraph
        from fastcausal.sem import edges_to_lavaan, run_semopy, add_sem_results_to_graph

        results, graph_info = run_algorithm(
            df, algorithm=algorithm, knowledge=knowledge, **kwargs
        )

        dg = build_dgraph(results["edges"])

        if run_sem and results["edges"]:
            lavaan_model = edges_to_lavaan(results["edges"])
            if lavaan_model.strip():
                sem_results = run_semopy(lavaan_model, df)
                results["sem_results"] = sem_results
                if sem_results and sem_results.get("estimates") is not None:
                    add_sem_results_to_graph(dg, sem_results["estimates"])

        return results, dg

    def run_stability(
        self,
        df: pd.DataFrame,
        algorithm: str = "gfci",
        runs: int = 100,
        min_fraction: float = 0.75,
        subsample_fraction: float = 0.9,
        knowledge: Optional[dict] = None,
        run_sem: bool = True,
        **kwargs,
    ) -> tuple[dict, DgraphFlex]:
        """
        Run bootstrapped stability analysis.

        Repeatedly subsamples the data and runs causal discovery,
        keeping only edges that appear in at least min_fraction of runs.

        Parameters
        ----------
        df : pd.DataFrame
            Continuous numeric data.
        algorithm : str
            One of "pc", "fges", "gfci".
        runs : int
            Number of bootstrap iterations.
        min_fraction : float
            Minimum fraction of runs an edge must appear in to be kept.
        subsample_fraction : float
            Fraction of rows to use in each subsample.
        knowledge : dict or None
            Prior knowledge dict.
        run_sem : bool
            If True, fit a SEM on stable edges.
        **kwargs
            Additional algorithm parameters.

        Returns
        -------
        results : dict
            Includes edges, edge counts/frequencies, and optionally SEM results.
        graph : DgraphFlex
            Graph of stable edges.
        """
        from fastcausal.search import run_algorithm
        from fastcausal.edges import select_edges, build_dgraph
        from fastcausal.sem import edges_to_lavaan, run_semopy, add_sem_results_to_graph
        from fastcausal.transform import subsample_df, standardize_df_cols

        try:
            from tqdm.auto import tqdm
        except ImportError:
            def tqdm(iterable, **kw):
                return iterable

        edge_counts: dict[str, int] = {}

        for i in tqdm(range(runs), desc="Stability search", unit="run"):
            sub_df = subsample_df(df, fraction=subsample_fraction)

            try:
                result_i, _ = run_algorithm(
                    sub_df, algorithm=algorithm, knowledge=knowledge, **kwargs
                )
                for edge in result_i["edges"]:
                    edge_counts[edge] = edge_counts.get(edge, 0) + 1
            except Exception:
                pass  # skip failed runs (e.g. singular matrix)

        # Convert counts to fractions
        sorted_keys = sorted(edge_counts.keys())
        sorted_edge_fractions = {e: edge_counts[e] / runs for e in sorted_keys}
        sorted_edge_counts_raw = {e: edge_counts[e] for e in sorted_keys}

        # Select stable edges
        selected_edges = select_edges(sorted_edge_fractions, min_fraction=min_fraction)

        # Build graph and optionally fit SEM
        dg = None
        sem_results = None

        if selected_edges:
            dg = build_dgraph(selected_edges)

            if run_sem:
                lavaan_model = edges_to_lavaan(selected_edges)
                if lavaan_model.strip():
                    sem_results = run_semopy(lavaan_model, df)
                    if sem_results and sem_results.get("estimates") is not None:
                        add_sem_results_to_graph(dg, sem_results["estimates"])

        results = {
            "edges": selected_edges,
            "sorted_edge_counts": sorted_edge_fractions,
            "sorted_edge_counts_raw": sorted_edge_counts_raw,
            "sem_results": sem_results,
            "algorithm": algorithm,
            "runs": runs,
            "min_fraction": min_fraction,
        }

        return results, dg

    # -- Visualization --

    def show_graph(
        self,
        dg: DgraphFlex,
        node_styles: Optional[list[dict]] = None,
        format: str = "png",
        res: int = 72,
        directed_only: bool = False,
    ):
        """Display a causal graph inline (Jupyter) or to screen.

        Parameters
        ----------
        dg : DgraphFlex
            Graph to display.
        node_styles : list of dict or None
            Pattern-based style rules (e.g. [{"pattern": "*_lag", "shape": "box"}]).
        format : str
            Image format.
        res : int
            Resolution in DPI.
        directed_only : bool
            If True, only show directed edges.

        Returns
        -------
        graphviz.Digraph
        """
        from fastcausal.viz.graphs import show_graph
        return show_graph(dg, node_styles=node_styles, format=format,
                          res=res, directed_only=directed_only)

    def save_graph(
        self,
        dg: DgraphFlex,
        pathname: str,
        node_styles: Optional[list[dict]] = None,
        plot_format: str = "png",
        res: int = 300,
        directed_only: bool = False,
    ):
        """Save a causal graph to file.

        Parameters
        ----------
        dg : DgraphFlex
            Graph to save.
        pathname : str
            Output path (without extension).
        node_styles : list of dict or None
            Pattern-based style rules.
        plot_format : str
            Output format.
        res : int
            Resolution in DPI.
        directed_only : bool
            If True, only include directed edges.
        """
        from fastcausal.viz.graphs import save_graph
        save_graph(dg, pathname, node_styles=node_styles,
                   plot_format=plot_format, res=res,
                   directed_only=directed_only)

    def show_n_graphs(
        self,
        graphs: list[DgraphFlex],
        node_styles: Optional[list[dict]] = None,
        labels: Optional[list[str]] = None,
        gray_disconnected: bool = True,
        directed_only: bool = False,
        graph_size: Optional[str] = None,
        **kwargs,
    ):
        """Display multiple graphs side-by-side with shared node positions.

        Parameters
        ----------
        graphs : list of DgraphFlex
            Graphs to compare.
        node_styles : list of dict or None
            Pattern-based style rules.
        labels : list of str or None
            Title for each graph.
        gray_disconnected : bool
            Gray out isolated nodes.
        directed_only : bool
            Only show directed edges.
        graph_size : str or None
            Size 'width,height' in inches.

        Returns
        -------
        list of graphviz.Digraph
        """
        from fastcausal.viz.graphs import show_n_graphs
        return show_n_graphs(graphs, node_styles=node_styles, labels=labels,
                             gray_disconnected=gray_disconnected,
                             directed_only=directed_only,
                             graph_size=graph_size, **kwargs)

    def save_n_graphs(
        self,
        graphs: list[DgraphFlex],
        pathnames: list[str],
        node_styles: Optional[list[dict]] = None,
        labels: Optional[list[str]] = None,
        gray_disconnected: bool = True,
        directed_only: bool = False,
        graph_size: Optional[str] = None,
        **kwargs,
    ):
        """Save multiple graphs with shared layout to files.

        Parameters
        ----------
        graphs : list of DgraphFlex
            Graphs to save.
        pathnames : list of str
            Output paths (without extension), one per graph.
        node_styles : list of dict or None
            Pattern-based style rules.
        labels : list of str or None
            Title for each graph.
        gray_disconnected : bool
            Gray out isolated nodes.
        directed_only : bool
            Only show directed edges.
        graph_size : str or None
            Size 'width,height' in inches.
        """
        from fastcausal.viz.graphs import save_n_graphs
        save_n_graphs(graphs, pathnames, node_styles=node_styles,
                      labels=labels, gray_disconnected=gray_disconnected,
                      directed_only=directed_only,
                      graph_size=graph_size, **kwargs)
