"""
Edge parsing, extraction, selection, and graph building utilities.
"""

import re
from typing import Any

from dgraph_flex import DgraphFlex


def extract_edges(text: str) -> list[str]:
    """
    Extract edge strings from Tetrad-format numbered output.

    Parses lines like:
        1. X --> Y
        2. A o-> B

    Parameters
    ----------
    text : str
        Raw text output containing numbered edges.

    Returns
    -------
    list of str
        Edge strings like ['X --> Y', 'A o-> B'].
    """
    edges = []
    pattern = re.compile(r"^\s*\d+\.\s+(.+)$")

    for line in text.strip().splitlines():
        match = pattern.match(line)
        if match:
            edge = match.group(1).strip()
            if any(op in edge for op in ["-->", "<--", "o->", "<-o", "o-o", "---", "<->"]):
                edges.append(edge)

    return edges


def select_edges(
    edge_counts: dict[str, float],
    min_fraction: float = 0.75,
) -> list[str]:
    """
    Select edges that appear above a minimum frequency threshold.

    Handles deduplication: when the same node pair appears with different
    edge types (e.g., A --> B and A o-> B), their frequencies are summed.
    The most frequent edge type is kept. Undirected edges are normalized
    so A o-o B and B o-o A are treated as the same pair.

    Parameters
    ----------
    edge_counts : dict
        Mapping of edge string to frequency (0.0 to 1.0).
    min_fraction : float
        Minimum frequency threshold.

    Returns
    -------
    list of str
        Filtered and deduplicated edge strings.
    """
    import pandas as pd

    if not edge_counts:
        return []

    # Parse edges into a DataFrame
    rows = []
    for edge, fraction in edge_counts.items():
        parts = edge.strip().split()
        if len(parts) == 3:
            rows.append({"src": parts[0], "edge_type": parts[1], "dest": parts[2], "fraction": fraction})

    if not rows:
        return []

    edge_df = pd.DataFrame(rows)
    selected_edges: dict[str, float] = {}

    # Process directed edges (-->, o->) separately from undirected
    directed_types = {"-->", "o->"}
    directed_df = edge_df[edge_df["edge_type"].isin(directed_types)].copy()
    undirected_df = edge_df[~edge_df["edge_type"].isin(directed_types)].copy()

    # --- Directed edges ---
    if not directed_df.empty:
        directed_df = directed_df.sort_values(
            by=["src", "dest", "fraction"], ascending=[True, True, False]
        )
        for (src, dest), group in directed_df.groupby(["src", "dest"]):
            if len(group) == 1:
                row = group.iloc[0]
                if row["fraction"] >= min_fraction:
                    selected_edges[f"{row['src']} {row['edge_type']} {row['dest']}"] = row["fraction"]
            else:
                fraction_sum = group["fraction"].sum()
                if fraction_sum >= min_fraction:
                    best = group.iloc[0]  # highest fraction
                    selected_edges[f"{best['src']} {best['edge_type']} {best['dest']}"] = float(fraction_sum)

    # --- Undirected edges (normalize order: alphabetically smaller node first) ---
    if not undirected_df.empty:
        for i in undirected_df.index:
            if undirected_df.loc[i, "src"] > undirected_df.loc[i, "dest"]:
                undirected_df.loc[i, "src"], undirected_df.loc[i, "dest"] = (
                    undirected_df.loc[i, "dest"],
                    undirected_df.loc[i, "src"],
                )

        undirected_df = undirected_df.sort_values(
            by=["src", "dest", "fraction"], ascending=[True, True, False]
        )
        for (src, dest), group in undirected_df.groupby(["src", "dest"]):
            if len(group) == 1:
                row = group.iloc[0]
                if row["fraction"] >= min_fraction:
                    selected_edges[f"{row['src']} {row['edge_type']} {row['dest']}"] = row["fraction"]
            else:
                fraction_sum = group["fraction"].sum()
                if fraction_sum >= min_fraction:
                    best = group.iloc[0]
                    selected_edges[f"{best['src']} {best['edge_type']} {best['dest']}"] = float(fraction_sum)

    return list(selected_edges.keys())


def build_dgraph(edges: list[str]) -> DgraphFlex:
    """
    Build a DgraphFlex graph from a list of edge strings.

    Parameters
    ----------
    edges : list of str
        Edge strings like ['X --> Y', 'A o-> B'].

    Returns
    -------
    DgraphFlex
        Graph with edges added.
    """
    dg = DgraphFlex()
    dg.add_edges(edges)
    return dg


def parse_edges_to_graph_info(
    edges: list[str],
    nodes: list[str],
) -> dict[str, Any]:
    """
    Parse edge strings into structured graph info.

    Parameters
    ----------
    edges : list of str
        Edge strings.
    nodes : list of str
        Node names.

    Returns
    -------
    dict
        Keys: adjacency, directed_edges, undirected_edges,
        bidirected_edges, partially_oriented_edges, circle_edges.
    """
    adjacency: dict[str, list[str]] = {n: [] for n in nodes}
    directed_edges: list[tuple[str, str]] = []
    undirected_edges: list[tuple[str, str]] = []
    bidirected_edges: list[tuple[str, str]] = []
    partially_oriented_edges: list[tuple[str, str, str]] = []
    circle_edges: list[tuple[str, str]] = []

    for edge_str in edges:
        parts = edge_str.strip().split()
        if len(parts) != 3:
            continue

        node1, edge_type, node2 = parts

        if node1 in adjacency:
            adjacency[node1].append(node2)
        if node2 in adjacency:
            adjacency[node2].append(node1)

        if edge_type == "-->":
            directed_edges.append((node1, node2))
        elif edge_type == "<--":
            directed_edges.append((node2, node1))
        elif edge_type == "---":
            undirected_edges.append((node1, node2))
        elif edge_type == "<->":
            bidirected_edges.append((node1, node2))
        elif edge_type == "o->":
            partially_oriented_edges.append((node1, edge_type, node2))
        elif edge_type == "o-o":
            circle_edges.append((node1, node2))

    return {
        "adjacency": adjacency,
        "directed_edges": directed_edges,
        "undirected_edges": undirected_edges,
        "bidirected_edges": bidirected_edges,
        "partially_oriented_edges": partially_oriented_edges,
        "circle_edges": circle_edges,
    }
