"""
SEM (Structural Equation Modeling) fitting via semopy.

Consolidated from fastcda and tetrad-port.
"""

from typing import Any, Optional

import pandas as pd

from dgraph_flex import DgraphFlex


def edges_to_lavaan(
    edges: list[str],
    include_types: Optional[list[str]] = None,
    include_covariances: bool = False,
) -> str:
    """
    Convert a list of edge strings to a lavaan/semopy model string.

    Parameters
    ----------
    edges : list of str
        Edge strings like 'X --> Y', 'A o-> B'.
    include_types : list of str or None
        Edge types to include as regression paths. Default: ['-->', 'o->'].
    include_covariances : bool
        If True, include ``---`` and ``<->`` edges as covariance (``~~``)
        terms. Default is False because PAG algorithms (GFCI, BOSS-FCI,
        GRaSP-FCI) use these edge types to indicate possible latent
        confounding, which cannot be properly represented as simple
        covariances in semopy's basic Model. Including them can also cause
        solver convergence failures (SLSQP "Inequality constraints
        incompatible") when the free covariance parameters conflict with
        variance constraints already implied by the regression structure.

    Returns
    -------
    str
        A lavaan-style model string compatible with semopy.
    """
    if include_types is None:
        include_types = ["-->", "o->"]

    regressions: dict[str, list[str]] = {}
    covariances: list[tuple[str, str]] = []

    for edge_str in edges:
        parts = edge_str.strip().split()
        if len(parts) != 3:
            continue

        node1, edge_type, node2 = parts

        if edge_type in include_types:
            regressions.setdefault(node2, []).append(node1)
        elif edge_type == "<--":
            regressions.setdefault(node1, []).append(node2)
        elif include_covariances and edge_type in ("---", "<->"):
            covariances.append((node1, node2))

    lines = []
    for child in sorted(regressions.keys()):
        parents = sorted(regressions[child])
        lines.append(f"{child} ~ {' + '.join(parents)}")

    for n1, n2 in sorted(covariances):
        lines.append(f"{n1} ~~ {n2}")

    return "\n".join(lines)


def run_semopy(
    lavaan_model: str,
    df: pd.DataFrame,
) -> Optional[dict[str, Any]]:
    """
    Fit a SEM model using semopy and return results.

    Parameters
    ----------
    lavaan_model : str
        Model in lavaan syntax (as produced by edges_to_lavaan).
    df : pd.DataFrame
        Data to fit the model on.

    Returns
    -------
    dict or None
        Keys: 'estimates' (pd.DataFrame), 'fit_stats' (dict or None),
        'model' (semopy.Model). Returns None if fitting fails.
    """
    try:
        import semopy
    except ImportError:
        raise ImportError(
            "semopy is required for SEM fitting. "
            "Install it with: pip install fastcausal[sem]"
        )

    try:
        model = semopy.Model(lavaan_model)
        model.fit(df)

        estimates = model.inspect()
        try:
            stats = semopy.calc_stats(model)
            fit_stats = stats.to_dict() if hasattr(stats, "to_dict") else stats
        except Exception:
            fit_stats = None

        return {
            "estimates": estimates,
            "fit_stats": fit_stats,
            "model": model,
        }
    except Exception:
        return None


def add_sem_results_to_graph(
    dg: DgraphFlex,
    estimates_df: pd.DataFrame,
) -> DgraphFlex:
    """
    Decorate a DgraphFlex graph with SEM coefficient colors and labels.

    Positive coefficients get green edges, negative get red.

    Parameters
    ----------
    dg : DgraphFlex
        Graph to decorate.
    estimates_df : pd.DataFrame
        SEM estimates from semopy (must have lval, op, rval, Estimate, p-value columns).

    Returns
    -------
    DgraphFlex
        The same graph object, modified in place.
    """
    if estimates_df is None:
        return dg

    for _, row in estimates_df.iterrows():
        if row.get("op") != "~":
            continue

        lval = row.get("lval", "")
        rval = row.get("rval", "")
        estimate = row.get("Estimate", 0.0)
        pvalue = row.get("p-value", 1.0)

        color = "green" if estimate >= 0 else "red"

        try:
            dg.modify_existing_edge(
                rval, lval,
                color=color,
                strength=round(estimate, 3),
                pvalue=round(pvalue, 4),
            )
        except Exception:
            pass

    return dg
