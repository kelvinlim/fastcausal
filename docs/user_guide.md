# User Guide

## Data Pipeline

The typical fastcausal workflow has five stages:

```
Load data → Transform → Knowledge → Search → Visualize
```

---

### 1. Load Data

```python
from fastcausal import FastCausal
fc = FastCausal()

# Built-in EMA dataset (Boston pain study, 14 variables, 640 rows)
df = fc.load_sample("boston")

# Or load your own CSV
df = fc.load_csv("mydata.csv")
```

---

### 2. Transform

```python
# Add lagged copies of each column (suffix '_lag')
df = fc.add_lag_columns(df, lag_stub='_lag')

# Standardize all columns (zero mean, unit variance)
df = fc.standardize(df)

# Optionally subsample rows (reproducible with seed)
df = fc.subsample(df, n=200, seed=42)
```

---

### 3. Prior Knowledge

Prior knowledge constrains the causal search using domain expertise.

#### Temporal tiers (most common)

For time-series data with lagged columns, use `create_lag_knowledge()`:

```python
# Lagged variables go in tier 0 (past), current variables in tier 1 (present)
knowledge = fc.create_lag_knowledge(df.columns)
```

This forbids any directed edge from present → past, encoding the arrow of time.

#### Custom knowledge dict

```python
knowledge = {
    # Temporal tiers: variables in lower tiers cannot be caused by higher tiers
    "addtemporal": {
        0: ["Age", "Genetics"],       # tier 0 (earliest / exogenous)
        1: ["Exercise", "Diet"],      # tier 1
        2: ["BMI", "BP"],             # tier 2 (latest / endogenous)
    },

    # Forbid specific directed edges
    "forbiddirect": [
        ("Exercise", "Age"),          # forbid Exercise -> Age
    ],

    # Require specific directed edges
    "requiredirect": [
        ("Smoking", "BP"),            # require Smoking -> BP
    ],

    # Forbid edges within a tier (opt-in)
    "forbidden_within": {0},          # no edges between tier-0 variables
}
```

#### Load from a Tetrad prior file

```python
from fastcausal.knowledge import read_prior_file
knowledge = read_prior_file("prior.txt")
```

---

### 4. Run Causal Search

#### Single search

```python
results, graph = fc.run_search(
    df,
    algorithm="gfci",
    alpha=0.01,
    penalty_discount=1.0,
    knowledge=knowledge,
)
```

`results` is a dict. `graph` is a `DgraphFlex` object.

#### Stability search (bootstrap)

Run the algorithm on many subsamples and keep only edges that appear frequently:

```python
results, graph = fc.run_stability(
    df,
    algorithm="gfci",
    alpha=0.01,
    penalty_discount=1.0,
    knowledge=knowledge,
    runs=50,
    min_fraction=0.75,       # keep edges found in ≥75% of runs
    subsample_fraction=0.9,
)
```

The `results["sorted_edge_counts"]` dict maps edge strings to fractions (0–1).

---

### 5. Visualize

```python
# Show graph inline (Jupyter)
fc.show_graph(graph)

# Save to PNG file
fc.save_graph(graph, "my_graph", plot_format="png")

# Show multiple graphs side by side
fc.show_n_graphs(
    [graph1, graph2, graph3],
    labels=["PD=1.0", "PD=2.0", "PD=3.0"],
    graph_size="10,8",
)
```

#### Node styling

Customize node appearance using a dict of style dicts:

```python
node_styles = {
    "PHQ9":    {"fillcolor": "lightblue", "style": "filled"},
    "PANAS_NA": {"fillcolor": "lightyellow", "style": "filled"},
}

fc.show_graph(graph, node_styles=node_styles)
```

---

## Results Dict

`run_search()` and `run_stability()` return `(results, graph)`.

| Key | Type | Present |
|-----|------|---------|
| `edges` | list[str] | Always |
| `nodes` | list[str] | Always |
| `num_edges` | int | Always |
| `num_nodes` | int | Always |
| `alpha` | float | PC, GFCI, BOSS-FCI, GRaSP-FCI |
| `penalty_discount` | float | FGES, GFCI, BOSS, BOSS-FCI, GRaSP, GRaSP-FCI |
| `sem_results` | dict | When `run_sem=True` |
| `sorted_edge_counts` | dict | `run_stability()` only |

---

## SEM Fitting

Structural equation model fitting is available via [semopy](https://semopy.com/). Pass `run_sem=True` to any search method:

```python
results, graph = fc.run_search(
    df,
    algorithm="gfci",
    alpha=0.01,
    run_sem=True,
)

# SEM estimates are in results["sem_results"]
# Edges in the graph are colored by SEM coefficient strength
fc.show_graph(graph)
```

---

## CLI

fastcausal includes a command-line interface:

```bash
# Run a causal search from the command line
fastcausal search --config config.yaml

# Show version
fastcausal --version
```

See [Migration from cda_tools2](migration_from_cda_tools2.md) for config file format details.
