# Migrating from fastcda to fastcausal

fastcausal is the successor to fastcda. It uses the same high-level workflow but with a cleaner API and no Java dependency (algorithms run via C++ bindings through `tetrad-port`).

## Installation

```bash
# Old
pip install fastcda

# New
pip install fastcausal
pip install "fastcausal[all]"   # include SEM, Jupyter, batch extras
```

## API mapping

| fastcda | fastcausal | Notes |
|---------|------------|-------|
| `FastCDA()` | `FastCausal()` | Same constructor |
| `fc.getEMAData()` | `fc.load_sample("boston")` | Same dataset |
| `fc.getSampleData()` | `fc.load_sample("boston")` | |
| `fc.read_csv(path)` | `fc.load_csv(path)` | Thin wrapper around `pd.read_csv` |
| `fc.add_lag_columns(df, lag_stub="_lag")` | `fc.add_lag_columns(df, lag_stub="_lag")` | Identical signature |
| `fc.standardize_df_cols(df)` | `fc.standardize(df)` | Renamed |
| `fc.subsample_df(df, fraction=0.9)` | `fc.subsample(df, fraction=0.9)` | Renamed |
| `fc.run_model_search(df, model="gfci", ...)` | `fc.run_search(df, algorithm="gfci", ...)` | See parameter changes below |
| `fc.run_stability_search(df, ...)` | `fc.run_stability(df, ...)` | Renamed |
| `fc.show_styled_graph(graph, node_styles)` | `fc.show_graph(graph, node_styles=node_styles)` | `node_styles` is now a keyword arg |
| `fc.save_styled_graph(graph, path, node_styles)` | `fc.save_graph(graph, path, node_styles=node_styles)` | Renamed |
| `fc.show_n_graphs(graphs, node_styles, ...)` | `fc.show_n_graphs(graphs, node_styles=node_styles, ...)` | Identical |
| `fc.save_n_graphs(graphs, paths, ...)` | `fc.save_n_graphs(graphs, paths, ...)` | Identical |
| `fc.load_knowledge(kdict)` | pass dict directly to `knowledge=` param | |
| `fc.create_lag_knowledge(cols)` | `fc.create_lag_knowledge(cols)` | Identical |
| `fc.edges_to_lavaan(edges)` | `fc.edges_to_lavaan(edges)` | Identical |
| `fc.run_semopy(model, df)` | `fc.run_sem(model, df)` | Renamed |

## Parameter changes for `run_search`

The old `run_model_search` accepted score/test as nested dicts. The new `run_search` uses flat keyword arguments:

```python
# fastcda (old)
result, graph = fc.run_model_search(
    df,
    model="gfci",
    score={"sem_bic": {"penalty_discount": 1.0}},
    test={"fisher_z": {"alpha": 0.05}},
    knowledge=knowledge,
)

# fastcausal (new)
result, graph = fc.run_search(
    df,
    algorithm="gfci",
    alpha=0.05,
    penalty_discount=1.0,
    knowledge=knowledge,
)
```

## Knowledge format

The knowledge dict format is unchanged:

```python
# Both fastcda and fastcausal accept this format:
knowledge = {
    "addtemporal": {
        0: ["alcohol_bev_lag", "PANAS_PA_lag", ...],   # tier 0: causes
        1: ["alcohol_bev", "PANAS_PA", ...],            # tier 1: effects
    }
}

# fastcausal also provides a helper:
knowledge = fc.create_lag_knowledge(df_original.columns)
```

## Return value changes

`run_search` (formerly `run_model_search`) now returns a dict with consistent keys:

```python
results = {
    "edges": ["X --> Y", "A o-> B"],   # list of edge strings
    "nodes": ["X", "Y", "A", "B"],
    "num_edges": 2,
    "num_nodes": 4,
    "algorithm": "gfci",
    "parameters": {"alpha": 0.05, "penalty_discount": 1.0},
    "sem_results": {                   # only if run_sem=True
        "estimates": pd.DataFrame,
        "fit_stats": dict,
    },
}
```

`run_stability` returns the same dict plus:

```python
{
    ...
    "sorted_edge_counts": {"X --> Y": 0.83, ...},   # edge -> fraction of runs
    "sorted_edge_counts_raw": {"X --> Y": 83, ...}, # edge -> count
    "runs": 100,
    "min_fraction": 0.5,
}
```

## Before/after example

```python
# ===== fastcda (old) =====
from fastcda import FastCDA

fc = FastCDA()
df = fc.getEMAData()
lag_stub = "_lag"
df_lag = fc.add_lag_columns(df, lag_stub=lag_stub)
df_std = fc.standardize_df_cols(df_lag)
cols = df.columns
knowledge = {"addtemporal": {0: [c + lag_stub for c in cols], 1: list(cols)}}

result, graph = fc.run_model_search(
    df_std,
    model="gfci",
    score={"sem_bic": {"penalty_discount": 1.0}},
    test={"fisher_z": {"alpha": 0.01}},
    knowledge=knowledge,
)
node_styles = [{"pattern": "*_lag", "style": "dotted"}]
fc.show_styled_graph(graph, node_styles)


# ===== fastcausal (new) =====
from fastcausal import FastCausal

fc = FastCausal()
df = fc.load_sample("boston")
df_lag = fc.add_lag_columns(df)
df_std = fc.standardize(df_lag)
knowledge = fc.create_lag_knowledge(df.columns)

result, graph = fc.run_search(
    df_std,
    algorithm="gfci",
    alpha=0.01,
    penalty_discount=1.0,
    knowledge=knowledge,
)
node_styles = [{"pattern": "*_lag", "style": "dotted"}]
fc.show_graph(graph, node_styles=node_styles)
```

## SEM is now automatic

In fastcda, SEM fitting required a separate call. In fastcausal, pass `run_sem=True` (the default) and SEM results are included in the returned dict and edges are colored automatically.

```python
# fastcausal: SEM runs automatically
result, graph = fc.run_search(df, algorithm="gfci", run_sem=True)
print(result["sem_results"]["estimates"])
```

## Node styling

Node style rules use the same `fnmatch` pattern format. The main change is that `node_styles` is now a keyword argument in `show_graph`/`save_graph`:

```python
node_styles = [
    {"pattern": "*_lag",        "style": "dotted"},
    {"pattern": "PANAS_PA*",    "style": "filled", "fillcolor": "lightgreen"},
    {"pattern": "PANAS_NA*",    "style": "filled", "fillcolor": "lightpink"},
    {"pattern": "alcohol_bev*", "shape": "box",    "style": "filled",
     "fillcolor": "purple",    "fontcolor": "white"},
]

# old: positional
fc.show_styled_graph(graph, node_styles)

# new: keyword
fc.show_graph(graph, node_styles=node_styles)
```
