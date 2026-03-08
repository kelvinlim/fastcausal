"""
Prior knowledge handling for causal discovery.

Converts user-facing dict format to tetrad-port Knowledge objects.
"""

from typing import Optional

from tetrad_port._tetrad_cpp import Knowledge


def create_lag_knowledge(
    columns: list[str],
    lag_stub: str = "_lag",
) -> dict:
    """
    Create a temporal knowledge dict for lagged data.

    Parameters
    ----------
    columns : list of str
        Original (non-lagged) column names.
    lag_stub : str
        The suffix used for lagged columns.

    Returns
    -------
    dict
        Knowledge dict with 'addtemporal' key.
        Tier 0 = lagged variables (past), Tier 1 = current variables.
    """
    lag_cols = [f"{c}{lag_stub}" for c in columns]
    return {"addtemporal": {0: lag_cols, 1: list(columns)}}


def read_prior_file(path: str) -> dict:
    """
    Read a prior knowledge file (Tetrad format) and return a knowledge dict.

    Parameters
    ----------
    path : str
        Path to the prior knowledge file.

    Returns
    -------
    dict
        Knowledge dict with 'addtemporal', 'forbiddirect',
        and/or 'requiredirect' keys.
    """
    knowledge: dict = {}
    current_section = None
    current_tier = None

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("/knowledge"):
                continue

            if line == "addtemporal":
                current_section = "addtemporal"
                knowledge.setdefault("addtemporal", {})
                continue

            if line == "forbiddirect":
                current_section = "forbiddirect"
                knowledge.setdefault("forbiddirect", [])
                continue

            if line == "requiredirect":
                current_section = "requiredirect"
                knowledge.setdefault("requiredirect", [])
                continue

            if current_section == "addtemporal":
                parts = line.split()
                if len(parts) >= 1 and parts[0].isdigit():
                    current_tier = int(parts[0])
                    tier_vars = parts[1:] if len(parts) > 1 else []
                    knowledge["addtemporal"].setdefault(current_tier, []).extend(tier_vars)
                elif current_tier is not None:
                    knowledge["addtemporal"][current_tier].extend(parts)

            elif current_section == "forbiddirect":
                parts = line.split()
                if len(parts) == 2:
                    knowledge["forbiddirect"].append(tuple(parts))

            elif current_section == "requiredirect":
                parts = line.split()
                if len(parts) == 2:
                    knowledge["requiredirect"].append(tuple(parts))

    return knowledge


def dict_to_knowledge(knowledge_dict: Optional[dict]) -> Optional[Knowledge]:
    """
    Convert a user-facing knowledge dict to a tetrad-port Knowledge object.

    Parameters
    ----------
    knowledge_dict : dict or None
        Knowledge dict with optional keys:
        - 'addtemporal': {tier_int: [var_names]}
        - 'forbiddirect': [(from_var, to_var), ...]
        - 'requiredirect': [(from_var, to_var), ...]

    Returns
    -------
    Knowledge or None
        tetrad-port Knowledge object, or None if input is None.
    """
    if knowledge_dict is None:
        return None

    k = Knowledge()

    if "addtemporal" in knowledge_dict:
        forbidden_within = knowledge_dict.get("forbidden_within", set())
        for tier, variables in knowledge_dict["addtemporal"].items():
            tier_int = int(tier)
            for var in variables:
                k.add_to_tier(tier_int, var)
            if tier_int in forbidden_within:
                k.set_tier_forbidden_within(tier_int, True)

    if "forbiddirect" in knowledge_dict:
        for from_var, to_var in knowledge_dict["forbiddirect"]:
            k.set_forbidden(from_var, to_var)

    if "requiredirect" in knowledge_dict:
        for from_var, to_var in knowledge_dict["requiredirect"]:
            k.set_required(from_var, to_var)

    return k
