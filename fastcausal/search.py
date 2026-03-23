"""
Thin wrapper around tetrad-port algorithms providing a unified search interface.
"""

from typing import Any, Optional

import pandas as pd

from tetrad_port import TetradPort

ALGORITHMS = ("pc", "fges", "gfci", "boss", "boss_fci", "grasp", "grasp_fci")


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
        One of "pc", "fges", "gfci", "boss", "boss_fci", "grasp",
        "grasp_fci".
    knowledge : dict or None
        Prior knowledge dict with 'addtemporal', 'forbiddirect',
        'requiredirect' keys. Converted to tetrad-port Knowledge object.

    Algorithm-Specific Parameters (via **kwargs)
    ---------------------------------------------
    PC (algorithm="pc"):
        alpha : float, default 0.05
            Significance level for Fisher Z independence tests.
            Lower values produce sparser graphs.
        depth : int, default -1
            Maximum conditioning set size. -1 = unlimited.

    FGES (algorithm="fges"):
        penalty_discount : float, default 1.0
            BIC penalty multiplier. Higher values produce sparser graphs.
        max_degree : int, default -1
            Maximum node degree. -1 = unlimited.
        faithfulness_assumed : bool, default True
            Skip the unfaithfulness phase (faster).

    GFCI (algorithm="gfci"):
        alpha : float, default 0.05
            Significance level for independence tests.
        penalty_discount : float, default 1.0
            BIC penalty for the initial FGES phase.
        depth : int, default -1
            Maximum conditioning set size.
        max_degree : int, default -1
            Maximum node degree.
        complete_rule_set : bool, default True
            Use Zhang's R1-R10 rules (True) or Spirtes' R1-R4 (False).
        max_disc_path_length : int, default -1
            Maximum discriminating path length for R4.

    BOSS (algorithm="boss"):
        penalty_discount : float, default 1.0
            BIC penalty multiplier.
        use_bes : bool, default False
            Run Backward Equivalence Search refinement.
        num_starts : int, default 1
            Number of random restarts.

    BOSS-FCI (algorithm="boss_fci"):
        alpha : float, default 0.05
            Significance level for independence tests.
        penalty_discount : float, default 1.0
            BIC penalty for BOSS scoring phase.
        depth : int, default -1
            Maximum conditioning set size.
        complete_rule_set : bool, default True
            Use Zhang's complete rules.
        use_bes : bool, default False
            Run BES refinement in BOSS.
        num_starts : int, default 1
            Number of random restarts for BOSS.

    GRaSP (algorithm="grasp"):
        penalty_discount : float, default 1.0
            BIC penalty multiplier.
        depth : int, default 3
            Max DFS depth for singular tucks.
        uncovered_depth : int, default 1
            Max depth for uncovered tucks.
        non_singular_depth : int, default 1
            Max depth for non-singular tucks.
        num_starts : int, default 1
            Number of random restarts.

    GRaSP-FCI (algorithm="grasp_fci"):
        alpha : float, default 0.05
            Significance level for independence tests.
        penalty_discount : float, default 1.0
            BIC penalty for GRaSP scoring phase.
        depth : int, default -1
            Maximum conditioning set size for FCI.
        grasp_depth : int, default 3
            Max DFS depth for GRaSP tucks.
        complete_rule_set : bool, default True
            Use Zhang's complete rules.
        num_starts : int, default 1
            Number of random restarts for GRaSP.

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
    elif algorithm == "boss":
        return tp.run_boss(df, knowledge=k, **kwargs)
    elif algorithm == "boss_fci":
        return tp.run_boss_fci(df, knowledge=k, **kwargs)
    elif algorithm == "grasp":
        return tp.run_grasp(df, knowledge=k, **kwargs)
    elif algorithm == "grasp_fci":
        return tp.run_grasp_fci(df, knowledge=k, **kwargs)
    else:
        raise ValueError(
            f"Unknown algorithm: {algorithm!r}. "
            f"Must be one of {ALGORITHMS}."
        )
