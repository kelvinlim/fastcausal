"""
Graph display and saving utilities.

Provides show_graph, save_graph, show_n_graphs, save_n_graphs.
Ported from fastcda's visualization code.
"""

from typing import Optional

from dgraph_flex import DgraphFlex

from fastcausal.viz.styling import (
    get_node_names,
    resolve_node_styles,
    apply_node_styles,
)


# ------------------------------------------------------------------
# Single graph display/save
# ------------------------------------------------------------------

def show_graph(
    dg: DgraphFlex,
    node_styles: Optional[list[dict]] = None,
    format: str = "png",
    res: int = 72,
    directed_only: bool = False,
):
    """Display a styled graph in a Jupyter notebook.

    Parameters
    ----------
    dg : DgraphFlex
        Graph with edges loaded.
    node_styles : list of dict or None
        Pattern-based style rules.
    format : str
        Image format (default 'png').
    res : int
        Resolution in DPI (default 72).
    directed_only : bool
        If True, only show directed edges.

    Returns
    -------
    graphviz.Digraph
        The rendered graphviz object.
    """
    import graphviz
    graphviz.set_jupyter_format(format)
    dg.load_graph(res=res, directed_only=directed_only)
    if node_styles:
        apply_node_styles(dg, node_styles)
    return dg.dot


def save_graph(
    dg: DgraphFlex,
    pathname: str,
    node_styles: Optional[list[dict]] = None,
    plot_format: str = "png",
    res: int = 300,
    cleanup: bool = True,
    directed_only: bool = False,
):
    """Save a styled graph to file.

    Parameters
    ----------
    dg : DgraphFlex
        Graph with edges loaded.
    pathname : str
        Output file path (without extension).
    node_styles : list of dict or None
        Pattern-based style rules.
    plot_format : str
        Output format (default 'png').
    res : int
        Resolution in DPI (default 300).
    cleanup : bool
        Remove intermediate Graphviz files.
    directed_only : bool
        If True, only include directed edges.
    """
    dg.load_graph(res=res, directed_only=directed_only)
    if node_styles:
        apply_node_styles(dg, node_styles)
    dg.gv_source = dg.dot.source
    with open(f"{pathname}.dot", 'w') as f:
        f.write(dg.gv_source)
    dg.dot.format = plot_format
    dg.dot.render(filename=pathname, format=plot_format, cleanup=cleanup)


# ------------------------------------------------------------------
# Multi-graph comparison with shared node layout
# ------------------------------------------------------------------

def _get_all_union_nodes(graphs: list[DgraphFlex]) -> list[str]:
    """Return sorted list of all unique node names across multiple graphs."""
    all_nodes = set()
    for dg in graphs:
        all_nodes.update(get_node_names(dg))
    return sorted(all_nodes)


def _build_union_dot(graphs: list[DgraphFlex], res: int = 300,
                     directed_only: bool = False):
    """Build a union graphviz.Digraph for computing shared layout."""
    from graphviz import Digraph as GvDigraph

    union_dot = GvDigraph(format='png')
    union_dot.attr(dpi=str(res), ranksep='1.5', nodesep='1.0')

    gvinit = graphs[0].graph.get('GENERAL', {}).get('gvinit', {})
    if 'nodes' in gvinit:
        union_dot.node_attr.update(gvinit['nodes'])

    seen_edges = set()
    for dg in graphs:
        for edge_key in dg.graph['GRAPH']['edges']:
            source, edge_type, target = edge_key.split(' ')
            if directed_only and edge_type not in ['-->', 'o->']:
                continue
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                union_dot.edge(source, target)

    for node in _get_all_union_nodes(graphs):
        union_dot.node(node)

    return union_dot


def _extract_positions(dot_obj) -> dict[str, tuple[str, str]]:
    """Extract node positions from graphviz by rendering to plain format."""
    plain_bytes = dot_obj.pipe(format='plain')
    plain_text = (plain_bytes.decode('utf-8')
                  if isinstance(plain_bytes, bytes) else plain_bytes)

    positions = {}
    for line in plain_text.splitlines():
        parts = line.split()
        if parts and parts[0] == 'node':
            node_name = parts[1]
            x = parts[2]
            y = parts[3]
            positions[node_name] = (x, y)

    return positions


def _apply_positions(dot_obj, positions: dict[str, tuple[str, str]]) -> None:
    """Pin nodes at fixed positions for neato rendering."""
    for node_name, (x, y) in positions.items():
        dot_obj.node(node_name, pos=f'{x},{y}!')


def _get_connected_nodes(dg: DgraphFlex, directed_only: bool = False) -> set[str]:
    """Return set of node names that have at least one edge."""
    connected = set()
    for edge_key in dg.graph['GRAPH']['edges']:
        source, edge_type, target = edge_key.split(' ')
        if directed_only and edge_type not in ['-->', 'o->']:
            continue
        connected.add(source)
        connected.add(target)
    return connected


def _apply_disconnected_styling(dot_obj, all_nodes: list[str],
                                connected_nodes: set[str]) -> None:
    """Gray out isolated nodes."""
    disconnected_attrs = {
        'fontcolor': '#BBBBBB',
        'color': '#DDDDDD',
        'fillcolor': '#F5F5F5',
        'style': 'filled',
    }
    for node in all_nodes:
        if node not in connected_nodes:
            dot_obj.node(node, **disconnected_attrs)


def _prepare_n_graphs(
    graphs: list[DgraphFlex],
    node_styles: Optional[list[dict]] = None,
    gray_disconnected: bool = True,
    res: int = 300,
    directed_only: bool = False,
    labels: Optional[list[str]] = None,
    graph_size: Optional[str] = None,
) -> list:
    """Prepare multiple graphs with shared node layout.

    Builds a union graph, computes positions, then pins them
    onto each individual graph.
    """
    union_dot = _build_union_dot(graphs, res=res, directed_only=directed_only)
    positions = _extract_positions(union_dot)
    all_nodes = _get_all_union_nodes(graphs)

    dots = []
    for idx, dg in enumerate(graphs):
        dg.load_graph(res=res, directed_only=directed_only)

        connected = _get_connected_nodes(dg, directed_only=directed_only)
        for node in all_nodes:
            if node not in connected:
                dg.dot.node(node)

        if node_styles:
            resolved = resolve_node_styles(all_nodes, node_styles)
            for node_name, attrs in resolved.items():
                str_attrs = {k: str(v) for k, v in attrs.items()}
                dg.dot.node(node_name, **str_attrs)

        if gray_disconnected:
            _apply_disconnected_styling(dg.dot, all_nodes, connected)

        _apply_positions(dg.dot, positions)
        dg.dot.engine = 'neato'
        dg.dot.attr(overlap='false', splines='true')

        if graph_size:
            dg.dot.attr(size=f'{graph_size}!', ratio='fill')

        if labels and idx < len(labels):
            dg.dot.attr(label=labels[idx], labelloc='t', fontsize='14')

        dots.append(dg.dot)

    return dots


def show_n_graphs(
    graphs: list[DgraphFlex],
    node_styles: Optional[list[dict]] = None,
    gray_disconnected: bool = True,
    format: str = "png",
    res: int = 72,
    directed_only: bool = False,
    labels: Optional[list[str]] = None,
    graph_size: Optional[str] = None,
) -> list:
    """Display multiple graphs side-by-side in Jupyter with shared layout.

    Parameters
    ----------
    graphs : list of DgraphFlex
        Graphs to display.
    node_styles : list of dict or None
        Pattern-based style rules.
    gray_disconnected : bool
        If True, gray out isolated nodes.
    format : str
        Image format.
    res : int
        Resolution in DPI.
    directed_only : bool
        If True, only show directed edges.
    labels : list of str or None
        Title labels, one per graph.
    graph_size : str or None
        Size string 'width,height' in inches.

    Returns
    -------
    list
        List of graphviz.Digraph objects.
    """
    import graphviz
    graphviz.set_jupyter_format(format)

    dots = _prepare_n_graphs(
        graphs,
        node_styles=node_styles,
        gray_disconnected=gray_disconnected,
        res=res,
        directed_only=directed_only,
        labels=labels,
        graph_size=graph_size,
    )

    try:
        from IPython.display import display, HTML
        import base64

        parts = []
        for dot in dots:
            img_bytes = dot.pipe(format=format, neato_no_op=True)
            if format == 'svg':
                parts.append(img_bytes.decode('utf-8'))
            else:
                b64 = base64.b64encode(img_bytes).decode('utf-8')
                parts.append(f'<img src="data:image/{format};base64,{b64}"/>')

        html = ('<div style="display:flex; gap:20px; '
                'align-items:flex-start; flex-wrap:wrap;">')
        for part in parts:
            html += f'<div>{part}</div>'
        html += '</div>'
        display(HTML(html))
    except ImportError:
        pass

    return dots


def save_n_graphs(
    graphs: list[DgraphFlex],
    pathnames: list[str],
    node_styles: Optional[list[dict]] = None,
    gray_disconnected: bool = True,
    plot_format: str = "png",
    res: int = 300,
    cleanup: bool = True,
    directed_only: bool = False,
    labels: Optional[list[str]] = None,
    graph_size: Optional[str] = None,
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
    gray_disconnected : bool
        If True, gray out isolated nodes.
    plot_format : str
        Output format.
    res : int
        Resolution in DPI.
    cleanup : bool
        Remove intermediate files.
    directed_only : bool
        If True, only include directed edges.
    labels : list of str or None
        Title labels, one per graph.
    graph_size : str or None
        Size string 'width,height' in inches.
    """
    if len(graphs) != len(pathnames):
        raise ValueError(
            f"Number of graphs ({len(graphs)}) must match "
            f"number of pathnames ({len(pathnames)})")

    dots = _prepare_n_graphs(
        graphs,
        node_styles=node_styles,
        gray_disconnected=gray_disconnected,
        res=res,
        directed_only=directed_only,
        labels=labels,
        graph_size=graph_size,
    )

    for dot, pathname in zip(dots, pathnames):
        with open(f"{pathname}.dot", 'w') as f:
            f.write(dot.source)
        dot.format = plot_format
        dot.render(filename=pathname, format=plot_format,
                   cleanup=cleanup, neato_no_op=True)
