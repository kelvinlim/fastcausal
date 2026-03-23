# Algorithm Guide

fastcausal provides access to seven causal discovery algorithms from the [Tetrad](https://github.com/cmu-phil/tetrad) project via [tetrad-port](https://github.com/kelvinlim/tetrad-port) (C++ bindings, no Java required).

## Algorithm Overview

| Algorithm | Type | Output | Latent Confounders | Best For |
|-----------|------|--------|--------------------|----------|
| **PC** | Constraint-based (Fisher Z) | CPDAG | No | Default when all variables are measured |
| **FGES** | Score-based (BIC) | CPDAG | No | Large, sparse graphs |
| **GFCI** | Hybrid (FGES + FCI rules) | PAG | Yes | General use; handles unmeasured confounders |
| **BOSS** | Permutation-based (BIC) | CPDAG | No | High precision for moderate sample sizes |
| **BOSS-FCI** | BOSS + FCI rules | PAG | Yes | High precision with latent confounders |
| **GRaSP** | Permutation-based (tuck DFS) | CPDAG | No | Very high precision, linear Gaussian data |
| **GRaSP-FCI** | GRaSP + FCI rules | PAG | Yes | Very high precision with latent confounders |

**CPDAG** = Completed Partially Directed Acyclic Graph (assumes no latent confounders).
**PAG** = Partial Ancestral Graph (allows for latent confounders).

## Choosing an Algorithm

- **Start with GFCI** if you suspect unmeasured confounders may exist. This is the most common real-world scenario.
- **Use FGES** for large, sparse graphs where speed matters and you believe all relevant variables are measured.
- **Use PC** as a baseline constraint-based approach when all variables are measured.
- **Use BOSS or GRaSP** when you want higher adjacency and orientation precision than FGES, especially with moderate sample sizes. These are newer permutation-based algorithms.
- **Use BOSS-FCI or GRaSP-FCI** for the same precision advantages as BOSS/GRaSP but when latent confounders may be present.

### Single Search vs Stability Search

- **`run_search()`** runs the algorithm once on the full dataset. Fast, deterministic, good for exploration.
- **`run_stability()`** runs the algorithm many times on subsampled data and keeps only edges that appear in at least `min_fraction` of runs (default 75%). More robust but slower. Recommended for final results.

```python
# Single search — quick exploration
results, graph = fc.run_search(df, algorithm="gfci", alpha=0.05)

# Stability search — robust final results
results, graph = fc.run_stability(
    df, algorithm="gfci", alpha=0.05,
    runs=100, min_fraction=0.75, subsample_fraction=0.9,
)
```

## Parameter Reference

### PC

Constraint-based algorithm using Fisher Z conditional independence tests.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `alpha` | 0.05 | Significance level. Lower = sparser graph, fewer false edges. |
| `depth` | -1 | Maximum conditioning set size. -1 = unlimited. |

```python
results, graph = fc.run_search(df, algorithm="pc", alpha=0.01)
```

### FGES

Score-based greedy search over Markov equivalence classes using BIC scoring.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `penalty_discount` | 1.0 | BIC penalty multiplier. Higher = sparser graph. |
| `max_degree` | -1 | Maximum node degree in output. -1 = unlimited. |
| `faithfulness_assumed` | True | Skip unfaithfulness phase (faster). |

```python
results, graph = fc.run_search(df, algorithm="fges", penalty_discount=2.0)
```

### GFCI

Hybrid algorithm combining FGES with FCI orientation rules. Handles latent confounders.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `alpha` | 0.05 | Significance level for independence tests. |
| `penalty_discount` | 1.0 | BIC penalty for the initial FGES phase. |
| `depth` | -1 | Maximum conditioning set size. |
| `max_degree` | -1 | Maximum node degree. |
| `complete_rule_set` | True | Zhang's R1-R10 (True) or Spirtes' R1-R4 (False). |
| `max_disc_path_length` | -1 | Maximum discriminating path length for R4. |
| `faithfulness_assumed` | True | Faithfulness assumption for the FGES phase. |

```python
results, graph = fc.run_search(df, algorithm="gfci", alpha=0.05, penalty_discount=1.0)
```

### BOSS

Permutation-based algorithm that finds optimal variable orderings using GrowShrink trees. High adjacency and orientation precision.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `penalty_discount` | 1.0 | BIC penalty multiplier. |
| `use_bes` | False | Run Backward Equivalence Search refinement. |
| `num_starts` | 1 | Number of random restarts. Best result returned. |
| `use_data_order` | True | Use column order for the first run. |

```python
results, graph = fc.run_search(df, algorithm="boss", penalty_discount=1.0)
```

### BOSS-FCI

BOSS combined with FCI orientation rules. Returns a PAG. Handles latent confounders.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `alpha` | 0.05 | Significance level for independence tests. |
| `penalty_discount` | 1.0 | BIC penalty for BOSS scoring phase. |
| `depth` | -1 | Maximum conditioning set size. |
| `complete_rule_set` | True | Use Zhang's complete rules R1-R10. |
| `max_disc_path_length` | -1 | Maximum discriminating path length for R4. |
| `use_bes` | False | Run BES refinement in BOSS. |
| `num_starts` | 1 | Number of random restarts. |

```python
results, graph = fc.run_search(df, algorithm="boss_fci", alpha=0.05)
```

### GRaSP

Permutation-based algorithm using depth-first tuck moves. Very high adjacency and orientation precision for linear Gaussian data.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `penalty_discount` | 1.0 | BIC penalty multiplier. |
| `depth` | 3 | Max DFS depth for singular tucks. |
| `uncovered_depth` | 1 | Max depth for uncovered tucks. |
| `non_singular_depth` | 1 | Max depth for non-singular tucks. |
| `ordered` | False | Enforce GRaSP0/1/2 ordering. |
| `num_starts` | 1 | Number of random restarts. |
| `use_data_order` | True | Use column order for the first run. |

```python
results, graph = fc.run_search(df, algorithm="grasp", penalty_discount=1.0)
```

### GRaSP-FCI

GRaSP combined with FCI orientation rules. Returns a PAG. Handles latent confounders.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `alpha` | 0.05 | Significance level for independence tests. |
| `penalty_discount` | 1.0 | BIC penalty for GRaSP scoring phase. |
| `depth` | -1 | Maximum conditioning set size for FCI. |
| `grasp_depth` | 3 | Max DFS depth for GRaSP tucks. |
| `uncovered_depth` | 1 | Max depth for uncovered tucks. |
| `non_singular_depth` | 1 | Max depth for non-singular tucks. |
| `ordered` | False | Enforce GRaSP ordering. |
| `complete_rule_set` | True | Use Zhang's complete rules R1-R10. |
| `max_disc_path_length` | -1 | Maximum discriminating path length for R4. |
| `num_starts` | 1 | Number of random restarts. |
| `use_data_order` | True | Use column order for the first run. |

```python
results, graph = fc.run_search(df, algorithm="grasp_fci", alpha=0.05)
```

## Edge Types

Algorithms return edges as strings like `"X --> Y"`. The edge type depends on whether the algorithm returns a CPDAG or PAG.

| Edge | Meaning | Graph Type |
|------|---------|------------|
| `X --> Y` | X causes Y (directed) | CPDAG, PAG |
| `X --- Y` | Undirected; direction ambiguous within the equivalence class | CPDAG, PAG |
| `X <-> Y` | Bidirected; latent common cause of X and Y | PAG only |
| `X o-> Y` | Partially oriented; circle endpoint means "could be tail or arrow" | PAG only |
| `X o-o Y` | Fully ambiguous orientation | PAG only |

**CPDAG algorithms** (PC, FGES, BOSS, GRaSP) produce `-->` and `---` edges only.

**PAG algorithms** (GFCI, BOSS-FCI, GRaSP-FCI) can produce all five edge types. The `o` (circle) endpoint indicates the algorithm could not determine whether it is an arrowhead or a tail.

## Prior Knowledge

Prior knowledge lets you encode domain expertise to constrain the search. All algorithms accept a `knowledge` parameter.

### Knowledge Dict Format

fastcausal uses a dict format with three optional keys:

```python
knowledge = {
    # Temporal tiers: variables in lower tiers cannot be caused by higher tiers
    "addtemporal": {
        0: ["Age", "Genetics"],      # tier 0 (earliest / exogenous)
        1: ["Exercise", "Diet"],      # tier 1
        2: ["BMI", "BP"],             # tier 2 (latest / endogenous)
    },

    # Forbidden directed edges
    "forbiddirect": [
        ("Exercise", "Age"),          # forbid Exercise -> Age
    ],

    # Required directed edges
    "requiredirect": [
        ("Smoking", "BP"),            # require Smoking -> BP
    ],

    # Optional: forbid edges within a tier
    "forbidden_within": {0},          # no edges between tier-0 variables
}
```

### Temporal Tiers for Lagged Data

The most common use case is time-series data with lagged columns. Use `create_lag_knowledge()` to automatically create the right tiers:

```python
fc = FastCausal()
df = fc.load_csv("timeseries.csv")
df = fc.add_lag_columns(df)

# Lagged variables go in tier 0 (past), current variables in tier 1
knowledge = fc.create_lag_knowledge(df.columns)

results, graph = fc.run_search(df, algorithm="gfci", knowledge=knowledge)
```

### Prior Knowledge Files

You can also load knowledge from a Tetrad-format prior file:

```python
from fastcausal.knowledge import read_prior_file
knowledge = read_prior_file("prior.txt")
results, graph = fc.run_search(df, algorithm="gfci", knowledge=knowledge)
```

Prior file format:

```
/knowledge
addtemporal
0 Age Genetics
1 Exercise Diet
2 BMI BP

forbiddirect
Exercise Age

requiredirect
Smoking BP
```

## Return Values

`run_search()` and `run_stability()` return `(results, graph)`.

### results dict

| Key | Type | Present |
|-----|------|---------|
| `edges` | list[str] | Always |
| `nodes` | list[str] | Always |
| `num_edges` | int | Always |
| `num_nodes` | int | Always |
| `alpha` | float | PC, GFCI, BOSS-FCI, GRaSP-FCI |
| `penalty_discount` | float | FGES, GFCI, BOSS, BOSS-FCI, GRaSP, GRaSP-FCI |
| `model_score` | float | FGES only |
| `sem_results` | dict | When `run_sem=True` |
| `sorted_edge_counts` | dict | `run_stability()` only — edge frequencies |
| `sorted_edge_counts_raw` | dict | `run_stability()` only — raw edge counts |

### graph (DgraphFlex)

The graph object can be passed directly to visualization methods:

```python
fc.show_graph(graph)
fc.save_graph(graph, "output", plot_format="png")
```

When `run_sem=True`, edges in the graph are decorated with SEM estimates (strength, p-value, color).
