"""
Node styling system using fnmatch patterns.

Ported from fastcda's node styling implementation. Rules are applied
in list order; later rules override earlier ones for the same node.
"""

import fnmatch

from dgraph_flex import DgraphFlex


def get_node_names(dg: DgraphFlex) -> list[str]:
    """Extract all unique node names from a DgraphFlex graph.

    Parameters
    ----------
    dg : DgraphFlex
        Graph with edges loaded.

    Returns
    -------
    list of str
        Sorted unique node names.
    """
    nodes = set()
    for key in dg.graph['GRAPH']['edges']:
        parts = key.split(' ')
        nodes.add(parts[0])
        nodes.add(parts[2])
    return sorted(nodes)


def resolve_node_styles(node_names: list[str], node_styles: list[dict]) -> dict[str, dict]:
    """Match node names against pattern-based style rules.

    Rules are applied in order. For each node, later matching rules
    override attributes set by earlier rules.

    Parameters
    ----------
    node_names : list of str
        Node names to match against.
    node_styles : list of dict
        Rule dicts, each with a 'pattern' key and Graphviz attributes.

    Returns
    -------
    dict
        Mapping node_name -> {attr: value} for matched nodes.
    """
    resolved = {}
    for node in node_names:
        attrs = {}
        for rule in node_styles:
            if fnmatch.fnmatchcase(node, rule['pattern']):
                attrs.update({k: v for k, v in rule.items() if k != 'pattern'})
        if attrs:
            resolved[node] = attrs
    return resolved


def apply_node_styles(dg: DgraphFlex, node_styles: list[dict]) -> None:
    """Apply per-node styling to a DgraphFlex graphviz object.

    Must be called after dg.load_graph() since load_graph()
    creates a fresh Digraph object.

    Parameters
    ----------
    dg : DgraphFlex
        Graph whose dg.dot has been created via load_graph().
    node_styles : list of dict
        Pattern-based style rule dicts.
    """
    node_names = get_node_names(dg)
    resolved = resolve_node_styles(node_names, node_styles)
    for node_name, attrs in resolved.items():
        str_attrs = {k: str(v) for k, v in attrs.items()}
        dg.dot.node(node_name, **str_attrs)
