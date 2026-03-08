"""
Graph metrics: ancestors, parent-child, degree centrality, path computation.

Ported from cda_tools2's graphmetrics.py.
"""

from typing import Optional

import pandas as pd


def create_networkx_graph(edges: list[str]):
    """
    Create a NetworkX DiGraph from edge strings.

    Parameters
    ----------
    edges : list of str
        Edge strings like ['X --> Y', 'A o-> B'].

    Returns
    -------
    networkx.DiGraph
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


def degree_centrality(edges: list[str]) -> dict[str, float]:
    """Compute degree centrality for nodes in a causal graph."""
    import networkx as nx
    G = create_networkx_graph(edges)
    return nx.degree_centrality(G)


def get_ancestors(edges: list[str], target_nodes: list[str]) -> dict[str, list[str]]:
    """
    Get all ancestor nodes for each target node.

    Parameters
    ----------
    edges : list of str
        Edge strings.
    target_nodes : list of str
        Nodes to find ancestors for.

    Returns
    -------
    dict
        Mapping target_node -> list of ancestor nodes.
    """
    import networkx as nx
    G = create_networkx_graph(edges)
    result = {}
    for node in target_nodes:
        if node in G:
            result[node] = list(nx.ancestors(G, node))
        else:
            result[node] = []
    return result


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
