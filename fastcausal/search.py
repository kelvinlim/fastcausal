"""
Thin wrapper around tetrad-port algorithms providing a unified search interface.
"""

from typing import Any, Optional

import pandas as pd

from tetrad_port import TetradPort


def run_algorithm(
    df: pd.DataFrame,
    algorithm: str = "gfci",
    knowledge: Optional[dict] = None,
    **kwargs,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Run a causal discovery algorithm.

    Parameters
    ----------
    df : pd.DataFrame
        Continuous numeric data.
    algorithm : str
        One of "pc", "fges", "gfci".
    knowledge : dict or None
        Prior knowledge dict with 'addtemporal', 'forbiddirect',
        'requiredirect' keys. Converted to tetrad-port Knowledge object.
    **kwargs
        Algorithm-specific parameters (alpha, penalty_discount, depth, etc.)

    Returns
    -------
    results : dict
        Search results including edges, nodes, counts.
    graph_info : dict
        Parsed edge information (adjacency, directed_edges, etc.)
    """
    from fastcausal.knowledge import dict_to_knowledge

    tp = TetradPort()
    k = dict_to_knowledge(knowledge) if knowledge else None

    if algorithm == "pc":
        return tp.run_pc(df, knowledge=k, **kwargs)
    elif algorithm == "fges":
        return tp.run_fges(df, knowledge=k, **kwargs)
    elif algorithm == "gfci":
        return tp.run_gfci(df, knowledge=k, **kwargs)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm!r}. Must be 'pc', 'fges', or 'gfci'.")
