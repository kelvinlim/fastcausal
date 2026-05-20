"""
Graph metrics: ancestors, parent-child, degree centrality, path computation.

Ported from cda_tools2's graphmetrics.py.
"""

from typing import Optional

import pandas as pd


def create_networkx_graph(edges: list[str]):
    """
    Create a NetworkX DiGraph from edge strings (for centrality/structural use).

    All edge types add directed edges from src to dest; non-directed types
    (``---``, ``o-o``, ``<->``) also add the reverse. Note: this representation
    is NOT correct for causal ancestor traversal — use
    :func:`_build_ancestor_digraph` for that.
    """
    try:
        import networkx as nx
    except ImportError:
        raise ImportError("networkx is required for graph metrics. pip install networkx")

    G = nx.DiGraph()
    for edge_str in edges:
        parts = edge_str.strip().split()
        if len(parts) != 3:
            continue
        src, edge_type, dest = parts
        if edge_type in ("-->", "o->"):
            G.add_edge(src, dest, edge_type=edge_type)
        elif edge_type in ("---", "o-o", "<->"):
            G.add_edge(src, dest, edge_type=edge_type)
            G.add_edge(dest, src, edge_type=edge_type)
    return G


def _build_ancestor_digraph(edges: list[str], mode: str):
    """
    Build a NetworkX DiGraph whose reverse-reachability matches PAG/CPDAG
    ancestor semantics.

    mode = "definite": only ``-->`` is walked (src → dest). Yields the set of
        nodes that MUST be ancestors in every DAG consistent with the PAG.
    mode = "possible": ``-->`` and ``o->`` are walked src → dest;
        ``---`` and ``o-o`` are walked in BOTH directions (orientation
        unidentified). ``<->`` is NEVER walked — it encodes a latent common
        cause, so neither endpoint is an ancestor of the other. Yields the
        set of nodes that MIGHT be ancestors in some consistent DAG.
    """
    import networkx as nx
    if mode not in ("definite", "possible"):
        raise ValueError(f"mode must be 'definite' or 'possible', got {mode!r}")

    G = nx.DiGraph()
    for edge_str in edges:
        parts = edge_str.strip().split()
        if len(parts) != 3:
            continue
        src, edge_type, dest = parts
        if edge_type == "-->":
            G.add_edge(src, dest)
        elif edge_type == "o->" and mode == "possible":
            G.add_edge(src, dest)
        elif edge_type in ("---", "o-o") and mode == "possible":
            G.add_edge(src, dest)
            G.add_edge(dest, src)
        # "<->" intentionally skipped under both modes
    return G


def degree_centrality(edges: list[str]) -> dict[str, float]:
    """Compute degree centrality for nodes in a causal graph."""
    import networkx as nx
    G = create_networkx_graph(edges)
    return nx.degree_centrality(G)


def get_ancestors(
    edges: list[str],
    target_nodes: list[str],
    mode: str = "possible",
) -> dict[str, list[str]]:
    """
    Get ancestor nodes for each target node under PAG/CPDAG semantics.

    Parameters
    ----------
    edges : list of str
        Edge strings.
    target_nodes : list of str
        Nodes to find ancestors for.
    mode : {"possible", "definite"}, default "possible"
        See :func:`_build_ancestor_digraph` for the traversal rules.

    Returns
    -------
    dict
        Mapping target_node -> list of ancestor nodes.
    """
    import networkx as nx
    G = _build_ancestor_digraph(edges, mode=mode)
    result = {}
    for node in target_nodes:
        if node in G:
            result[node] = list(nx.ancestors(G, node))
        else:
            result[node] = []
    return result


def get_ancestor_subgraph(graph, nodes: list[str], mode: str = "possible"):
    """
    Build a subgraph containing the target nodes and all their ancestors.

    Parameters
    ----------
    graph : DgraphFlex
        Graph returned by ``FastCausal.run_search`` (or any DgraphFlex).
    nodes : list of str
        Target node names.
    mode : {"possible", "definite"}, default "possible"
        Ancestor semantics. ``"possible"`` walks ``-->`` and ``o->``
        forward and ``---`` / ``o-o`` in both directions; ``<->`` is
        never walked (it encodes a latent common cause).
        ``"definite"`` walks only ``-->``.

    Returns
    -------
    DgraphFlex
        New graph containing only edges whose endpoints both lie in
        ``targets ∪ ancestors(targets)``. Edge properties (color,
        strength, pvalue from SEM decoration) are preserved.
    """
    import networkx as nx
    from dgraph_flex import DgraphFlex

    edge_strings = list(graph.edges.keys())
    G = _build_ancestor_digraph(edge_strings, mode=mode)

    keep: set[str] = set(nodes)
    for node in nodes:
        if node in G:
            keep.update(nx.ancestors(G, node))

    sub = DgraphFlex()
    for edge_str, edge_data in graph.edges.items():
        parts = edge_str.strip().split()
        if len(parts) != 3:
            continue
        src, _, dest = parts
        if src in keep and dest in keep:
            sub.edges[edge_str] = edge_data
    return sub


def get_parent_child_edges(
    edges: list[str],
    parents: list[str],
    children: list[str],
) -> list[str]:
    """
    Extract edges between specified parent and child node sets.

    Parameters
    ----------
    edges : list of str
        All edge strings.
    parents : list of str
        Parent node names.
    children : list of str
        Child node names.

    Returns
    -------
    list of str
        Matching edge strings.
    """
    matching = []
    for edge_str in edges:
        parts = edge_str.strip().split()
        if len(parts) != 3:
            continue
        src, edge_type, dest = parts
        if src in parents and dest in children:
            matching.append(edge_str)
        elif dest in parents and src in children and edge_type in ("<--",):
            matching.append(edge_str)
    return matching


def compute_effect_sizes(
    sem_estimates: pd.DataFrame,
    edges: list[str],
) -> dict[str, float]:
    """
    Extract effect sizes from SEM estimates for each edge.

    Parameters
    ----------
    sem_estimates : pd.DataFrame
        SEM estimates from semopy.
    edges : list of str
        Edge strings.

    Returns
    -------
    dict
        Mapping edge_string -> effect size (SEM estimate).
    """
    effect_sizes = {}
    if sem_estimates is None:
        return effect_sizes

    for _, row in sem_estimates.iterrows():
        if row.get("op") != "~":
            continue
        lval = row.get("lval", "")
        rval = row.get("rval", "")
        estimate = row.get("Estimate", 0.0)

        # Match against edges
        for edge_str in edges:
            parts = edge_str.strip().split()
            if len(parts) != 3:
                continue
            src, _, dest = parts
            if src == rval and dest == lval:
                effect_sizes[edge_str] = estimate
                break

    return effect_sizes
