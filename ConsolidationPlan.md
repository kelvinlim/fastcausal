# Consolidation Plan: Implementing Approach A (Layered Packages)

This document details the implementation plan for combining cda_tools2, fastcda, dgraph_flex, and tetrad-port into a unified `fastcausal` package using the layered architecture described in ConsolidationRecommendation.md.

## Decisions (2026-03-07)

- **Repository:** github.com/kelvinlim/fastcausal at /home/kolim/Projects/fastcausal/
- **Python version:** >=3.11
- **CLI framework:** click
- **knowledge default:** `None` (no auto-detection; `_lag` suffix may not be used in future)
- **Config version:** Introduce v5.0 format; accept v4.0 with deprecation warning
- **tetrad-port PyPI:** Publication in progress (cibuildwheel configured)

## Implementation Status

| Phase | Status | Date |
|-------|--------|------|
| Phase 1: Foundation | **Complete** | 2026-03-07 |
| Phase 2: Core API | **Complete** | 2026-03-07 |
| Phase 3: Visualization | **Complete** | 2026-03-07 |
| Phase 4: Batch Pipeline and CLI | **Complete** | 2026-03-07 |
| Phase 5: Testing and Documentation | **Complete** | 2026-03-07 |
| Phase 6: Publication and Deprecation | Pending | — |

### Test Suite Summary (130 tests)

| Test file | Tests | Coverage area |
|-----------|-------|---------------|
| test_pipeline.py | 33 | parse steps, metrics, paths effect matrix |
| test_knowledge.py | 14 | lag knowledge, prior file parsing, dict_to_knowledge |
| test_config.py | 14 | v5 loading, v4→v5 migration, directories, params |
| test_viz.py | 13 | node styling (fnmatch), graph rendering, save/show |
| test_cli.py | 12 | help output, version, required args, analyze command |
| test_core.py | 11 | data loading, transforms, search, end-to-end workflow |
| test_transform.py | 10 | lag columns, standardize, subsample, jitter |
| test_edges.py | 9 | edge extraction, selection/dedup, graph info parsing |
| test_search.py | 8 | PC, FGES, GFCI execution, knowledge, parameters |
| test_sem.py | 6 | lavaan model conversion |

All 119 tests pass; 11 are skipped (require optional `networkx` dependency).

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Package Structure](#2-package-structure)
3. [API Design](#3-api-design)
4. [Phase 1: Foundation](#phase-1-foundation)
5. [Phase 2: Core API](#phase-2-core-api)
6. [Phase 3: Visualization](#phase-3-visualization)
7. [Phase 4: Batch Pipeline and CLI](#phase-4-batch-pipeline-and-cli)
8. [Phase 5: Testing and Documentation](#phase-5-testing-and-documentation)
9. [Phase 6: Publication and Deprecation](#phase-6-publication-and-deprecation)
10. [Utility Consolidation Map](#utility-consolidation-map)
11. [Config.yaml Compatibility](#configyaml-compatibility)
12. [Risk Register](#risk-register)

---

## 1. Architecture Overview

```
User installs: pip install fastcausal
                    |
                fastcausal  (API + CLI + viz + SEM + batch)
               /          \
        tetrad-port      dgraph_flex
        (C++ algorithms)   (graph rendering)
           |                    |
        nanobind/numpy      graphviz
```

**Dependency versions at time of plan:**
- tetrad-port: 0.1.0 (PC, FGES, GFCI implemented)
- dgraph_flex: 0.1.11
- fastcda: 0.1.21 (to be deprecated)
- cda_tools2: unversioned scripts (to be archived)

---

## 2. Package Structure

```
fastcausal/
├── pyproject.toml
├── README.md
├── CLAUDE.md
├── fastcausal/
│   ├── __init__.py              # exports FastCausal, version
│   ├── core.py                  # FastCausal class (main user-facing API)
│   ├── search.py                # thin wrapper around tetrad-port algorithms
│   ├── sem.py                   # SEM fitting via semopy
│   ├── transform.py             # lag columns, standardization, subsampling, jitter
│   ├── knowledge.py             # prior knowledge handling (temporal tiers, forbidden/required)
│   ├── edges.py                 # edge parsing, extraction, selection, deduplication
│   │
│   ├── viz/
│   │   ├── __init__.py
│   │   ├── styling.py           # node styling system (fnmatch patterns)
│   │   ├── graphs.py            # show_graph, save_graph, show_n_graphs, save_n_graphs
│   │   └── plots.py             # heatmaps, effect size grids, adjacency matrices
│   │
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── config.py            # YAML config parsing (v4.0 format)
│   │   ├── parse.py             # data preparation engine (from run_parse2.py)
│   │   ├── batch.py             # batch causal discovery across cases
│   │   ├── paths.py             # path/effect size analysis (from paths_plotdist2.py)
│   │   ├── report.py            # docx report generation (from create_docx_proj.py)
│   │   └── metrics.py           # graph metrics, ancestors, parent-child (from graphmetrics.py)
│   │
│   ├── io/
│   │   ├── __init__.py
│   │   ├── data.py              # CSV loading, bundled sample datasets
│   │   └── wearables.py         # fitbit/garmin integration (from cda_tools2)
│   │
│   ├── cli.py                   # CLI entry points (click-based)
│   │
│   └── data/                    # bundled sample datasets
│       ├── boston_data_raw.csv
│       └── boston_prior.txt
│
├── tests/
│   ├── test_core.py             # FastCausal API tests
│   ├── test_search.py           # algorithm wrapper tests
│   ├── test_sem.py              # SEM fitting tests
│   ├── test_transform.py        # data transformation tests
│   ├── test_knowledge.py        # prior knowledge tests
│   ├── test_edges.py            # edge parsing tests
│   ├── test_viz.py              # visualization tests
│   ├── test_pipeline.py         # batch pipeline tests
│   └── test_cli.py              # CLI integration tests
│
├── examples/
│   └── notebooks/
│       ├── quickstart.ipynb     # 5-minute intro
│       ├── ema_analysis.ipynb   # EMA workflow (replaces fastcda_demo)
│       └── batch_project.ipynb  # config-driven batch (replaces cda_tools2 workflow)
│
└── docs/
    ├── migration_from_fastcda.md
    └── migration_from_cda_tools2.md
```

---

## 3. API Design

### 3.1 Interactive API (Jupyter / scripting)

The `FastCausal` class is the single entry point, modeled on graphicalVAR's simplicity.

```python
from fastcausal import FastCausal

fc = FastCausal()

# Load data
df = fc.load_sample("boston")                    # bundled dataset
df = fc.load_csv("path/to/data.csv")            # user data

# Transform
df = fc.add_lag_columns(df)                      # add _lag columns
df = fc.standardize(df)                          # z-score

# Single search
results, graph = fc.run_search(
    df,
    algorithm="gfci",                            # "pc", "fges", "gfci"
    alpha=0.05,
    penalty_discount=1.0,
    knowledge=fc.create_lag_knowledge(df.columns), # temporal tiers
    run_sem=True,                                # fit SEM automatically
)

# Stability search (bootstrapped)
results, graph = fc.run_stability(
    df,
    algorithm="gfci",
    runs=100,
    min_fraction=0.75,
    subsample_fraction=0.9,
    run_sem=True,
)

# Visualize
fc.show_graph(graph, node_styles=[
    {"pattern": "*_lag", "shape": "box", "fillcolor": "lightyellow"},
    {"pattern": "PANAS_*", "fillcolor": "lightblue"},
])
fc.save_graph(graph, "my_result", format="png")

# Compare across parameters
fc.show_n_graphs(
    [graph1, graph2, graph3],
    labels=["PD=1", "PD=2", "PD=3"],
    directed_only=True,
)
```

### 3.2 Method mapping from existing packages

| FastCausal method | Source | Original method |
|-------------------|--------|-----------------|
| `load_sample()` | fastcda | `getEMAData()`, `getSampleData()` |
| `load_csv()` | fastcda | `read_csv()` |
| `add_lag_columns()` | fastcda/tetrad-port | `add_lag_columns()` |
| `standardize()` | fastcda/tetrad-port | `standardize_df_cols()` |
| `subsample()` | fastcda | `subsample_df()` |
| `run_search()` | **new** | combines `run_model_search()` pattern with tetrad-port backend |
| `run_stability()` | fastcda | `run_stability_search()` |
| `show_graph()` | fastcda | `show_styled_graph()` |
| `save_graph()` | fastcda | `save_styled_graph()` |
| `show_n_graphs()` | fastcda | `show_n_graphs()` |
| `save_n_graphs()` | fastcda | `save_n_graphs()` |
| `edges_to_lavaan()` | fastcda/tetrad-port | `edges_to_lavaan()` |
| `run_sem()` | fastcda/tetrad-port | `run_semopy()` |
| `load_knowledge()` | fastcda | `load_knowledge()` |
| `create_lag_knowledge()` | fastcda/tetrad-port | `create_lag_knowledge()` |

### 3.3 CLI Design

```bash
# Data preparation (replaces run_parse2.py)
fastcausal parse --config proj_ema/config.yaml

# Causal discovery batch (replaces run_causal2.py / run_causal3.py)
fastcausal run --config proj_ema/config.yaml
fastcausal run --config proj_ema/config.yaml --start 0 --end 85
fastcausal run --config proj_ema/config.yaml --list

# Path/effect size analysis (replaces paths_plotdist2.py)
fastcausal paths --config proj_ema/config.yaml

# Report generation (replaces create_docx_proj.py)
fastcausal report --config proj_ema/config.yaml --mode 2wide --stub _label.png

# Quick single-file analysis (new convenience command)
fastcausal analyze data.csv --algorithm gfci --alpha 0.05 --output results/
```

Entry point in pyproject.toml:
```toml
[project.scripts]
fastcausal = "fastcausal.cli:main"
```

### 3.4 Return value design

`run_search()` and `run_stability()` return `(results_dict, DgraphFlex)`:

```python
results = {
    "edges": ["X --> Y", "A o-> B"],         # edge strings
    "nodes": ["X", "Y", "A", "B"],           # node list
    "num_edges": 2,
    "num_nodes": 4,
    "algorithm": "gfci",
    "parameters": {"alpha": 0.05, ...},       # algorithm params used
    "sem_results": {                          # if run_sem=True
        "estimates": pd.DataFrame,
        "fit_stats": dict,
    },
    # stability-specific (only for run_stability)
    "sorted_edge_counts": {...},              # edge -> frequency
    "runs": 100,
    "min_fraction": 0.75,
    "cda_output": "...",                      # raw algorithm output
}
```

The DgraphFlex graph object is returned with edges already decorated with SEM results (strength, p-value, color) when `run_sem=True`.

---

## Phase 1: Foundation ✅

**Goal:** Get tetrad-port on PyPI and create the fastcausal skeleton.

### 1.1 Publish tetrad-port to PyPI

- Set up cibuildwheel CI for pre-built wheels
  - Target platforms: manylinux (x86_64, aarch64), macOS (x86_64, arm64), Windows (x86_64)
  - Use GitHub Actions workflow
- Ensure `pip install tetrad-port` works without a local C++ compiler on supported platforms
- Add sdist fallback for source builds on unsupported platforms
- Verify dgraph_flex is already on PyPI (it is, version 0.1.11)

### 1.2 Create fastcausal repository and skeleton

- Initialize repo with pyproject.toml:

```toml
[build-system]
requires = ["setuptools>=61.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "fastcausal"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "tetrad-port>=0.1.0",
    "dgraph_flex>=0.1.11",
    "pandas>=1.5",
    "numpy>=1.21",
    "scikit-learn>=1.0",
    "PyYAML>=6.0",
    "tqdm>=4.60",
    "graphviz>=0.20",
]

[project.optional-dependencies]
sem = ["semopy>=2.3"]
jupyter = ["ipykernel", "ipywidgets", "ipython", "matplotlib", "seaborn"]
batch = ["python-docx>=0.8", "pillow>=9.0"]
all = ["fastcausal[sem,jupyter,batch]"]
dev = ["fastcausal[all]", "pytest>=7.0", "click>=8.0"]

[project.scripts]
fastcausal = "fastcausal.cli:main"
```

- Create empty module structure per Section 2
- Write `__init__.py` with `from fastcausal.core import FastCausal`
- Add CLAUDE.md with project conventions

### 1.3 Deliverable

- `pip install tetrad-port` works on Linux/macOS/Windows
- `pip install fastcausal` installs but only has skeleton
- All existing packages continue to work unchanged

---

## Phase 2: Core API ✅

**Goal:** Implement `FastCausal` class with search, SEM, and data transformation — replacing fastcda for interactive use.

### 2.1 Implement transform.py

Port from fastcda and tetrad-port (consolidating the duplicated code):

- `add_lag_columns(df, columns=None, n_lags=1, lag_stub="_lag")` -> pd.DataFrame
- `standardize_df_cols(df, columns=None)` -> pd.DataFrame
- `subsample_df(df, fraction=0.9)` -> pd.DataFrame
- `create_permuted_dfs(df, n)` -> list[pd.DataFrame]
- `add_jitter(df, scale=0.0001)` -> pd.DataFrame

### 2.2 Implement knowledge.py

Port from fastcda's knowledge system, converting to tetrad-port's Knowledge object:

- `create_lag_knowledge(columns, lag_stub)` -> dict
- `load_knowledge(knowledge_dict)` -> tetrad_port.Knowledge
- `read_prior_file(path)` -> dict
- Internal: convert fastcda-style dict format to tetrad-port Knowledge C++ object

Key design decision: fastcda uses a dict format `{"addtemporal": {0: [...], 1: [...]}}` which gets translated to Java Knowledge calls. tetrad-port has a C++ Knowledge class exposed via nanobind. The `knowledge.py` module bridges these — it accepts the same dict format users know from fastcda and converts it to tetrad-port's Knowledge object internally.

### 2.3 Implement edges.py

Port from fastcda's edge handling:

- `extract_edges(text)` -> list[str] (regex parsing of numbered edges)
- `select_edges(edge_counts, min_fraction)` -> list[str] (deduplication for stability)
- `parse_edges_to_graph_info(edges, nodes)` -> dict (from tetrad-port)

### 2.4 Implement sem.py

Consolidate from fastcda and tetrad-port:

- `edges_to_lavaan(edges, include_types=["-->", "o->"])` -> str
- `run_semopy(lavaan_model, df)` -> dict
- `add_sem_results_to_graph(dg, estimates_df)` -> DgraphFlex

The `include_types` parameter maps to cda_tools2's `SEM.include_model_edges` config.

### 2.5 Implement search.py

Thin wrapper around tetrad-port that provides a unified interface:

```python
def run_algorithm(df, algorithm="gfci", knowledge=None, **kwargs):
    """
    Unified search interface.

    algorithm: "pc", "fges", "gfci"
    Returns: (results_dict, list_of_edge_strings)
    """
    tp = TetradPort()
    k = _convert_knowledge(knowledge)  # dict -> Knowledge object

    if algorithm == "pc":
        return tp.run_pc(df, knowledge=k, **kwargs)
    elif algorithm == "fges":
        return tp.run_fges(df, knowledge=k, **kwargs)
    elif algorithm == "gfci":
        return tp.run_gfci(df, knowledge=k, **kwargs)
```

### 2.6 Implement core.py — FastCausal class

The main user-facing class that composes all the above:

```python
class FastCausal:
    def __init__(self, verbose=1):
        self.verbose = verbose
        self.node_styles = []

    # Data loading
    def load_sample(self, name="boston") -> pd.DataFrame
    def load_csv(self, path) -> pd.DataFrame

    # Data transformation (delegates to transform.py)
    def add_lag_columns(self, df, ...) -> pd.DataFrame
    def standardize(self, df, ...) -> pd.DataFrame
    def subsample(self, df, ...) -> pd.DataFrame

    # Search (delegates to search.py + sem.py + edges.py)
    def run_search(self, df, algorithm="gfci", run_sem=True,
                   knowledge="auto", **kwargs) -> (dict, DgraphFlex)
    def run_stability(self, df, algorithm="gfci", runs=100,
                      min_fraction=0.75, run_sem=True,
                      knowledge="auto", **kwargs) -> (dict, DgraphFlex)

    # Knowledge (delegates to knowledge.py)
    def load_knowledge(self, knowledge_dict)
    def create_lag_knowledge(self, columns, lag_stub="_lag") -> dict

    # SEM (delegates to sem.py)
    def edges_to_lavaan(self, edges) -> str
    def run_sem(self, lavaan_model, df) -> dict

    # Visualization (delegates to viz/ — Phase 3)
    def show_graph(self, dg, node_styles=None, ...)
    def save_graph(self, dg, pathname, node_styles=None, ...)
    def show_n_graphs(self, graphs, labels=None, ...)
    def save_n_graphs(self, graphs, pathnames, ...)
```

The `knowledge` parameter defaults to `None` (no prior knowledge). Users explicitly pass a knowledge dict or call `create_lag_knowledge()` when needed. An `"auto"` option may be added in future but is not the default since `_lag` suffix conventions may change.

### 2.7 Implement io/data.py

- Bundle boston_data_raw.csv and boston_prior.txt from fastcda
- `load_sample(name)` returns a DataFrame from bundled data
- `load_csv(path)` is a thin wrapper around pd.read_csv with sensible defaults

### 2.8 Deliverable

- `FastCausal` class works for interactive Jupyter use
- All search algorithms (PC, FGES, GFCI) accessible through single API
- SEM fitting integrated
- No Java required
- Unit tests for all modules

---

## Phase 3: Visualization ✅

**Goal:** Port fastcda's visualization capabilities, using dgraph_flex as the rendering engine.

### 3.1 Implement viz/styling.py

Port from fastcda (lines 965-1103):

- `resolve_node_styles(nodes, style_rules)` -> dict mapping node -> style
- `apply_node_styles(dg, node_styles)` -> DgraphFlex
- fnmatch-based pattern matching for node styling rules
- Layered application (later rules override earlier)

### 3.2 Implement viz/graphs.py

Port from fastcda (lines 1104-1464):

- `show_graph(dg, node_styles, format, res, directed_only)` — inline Jupyter display
- `save_graph(dg, pathname, node_styles, format, res, directed_only)` — save to file
- `show_n_graphs(graphs, node_styles, labels, gray_disconnected, directed_only, graph_size)` — multi-graph comparison with shared node positions
- `save_n_graphs(graphs, pathnames, node_styles, ...)` — save multi-graph

Key implementation detail: multi-graph comparison uses neato engine with fixed positions so nodes align across graphs. This logic is in fastcda and must be ported carefully.

### 3.3 Implement viz/plots.py

Reusable plotting functions extracted from cda_tools2's paths_plotdist2.py (~1324 lines). These are the lower-level drawing functions that Phase 4's pipeline orchestrates:

- `plot_effect_size_heatmap(effect_data, src_vars, des_var, cases, **kwargs)` — single heatmap of effect sizes for one destination variable across cases and source variables
- `plot_effect_size_grid(heatmaps, layout, **kwargs)` — arrange multiple heatmaps into a grid with shared color scale, custom ordering, labels, and sizing (maps to cda_tools2's grid config: `titleSize`, `labelsize`, `widthInches`, `heightInches`, `reorderColumns`, `reorderCases`, `xrotate`)
- `plot_adjacency_matrix(edges, nodes, **kwargs)` — adjacency matrix visualization
- `save_plot(fig, pathname, format="png", dpi=300)` — save any plot to file

These are optional capabilities, gated behind the `jupyter` extra (matplotlib, seaborn).

Note: The config-driven orchestration that reads `pathsdata.json` and the PATHS section of config.yaml to call these functions lives in `pipeline/paths.py` (Phase 4, section 4.4).

### 3.4 Deliverable

- All fastcda visualization features work with tetrad-port backend
- Node styling, multi-graph comparison functional
- Reusable heatmap/adjacency plotting functions available for both interactive and batch use

---

## Phase 4: Batch Pipeline and CLI ✅

**Goal:** Port cda_tools2's config-driven batch processing into fastcausal CLI commands.

### 4.1 Implement pipeline/config.py

Port config.yaml parsing from cda_tools2:

- Parse v5.0 config format (GLOBAL, PREP, CAUSAL, SEM, GRAPHS, PATHS sections)
- Accept v4.0 format with deprecation warning and automatic mapping of `causal-cmd` sub-key to flat format
- Validate config structure
- Resolve directory paths relative to project folder

```yaml
# v5.0 (new default)
GLOBAL:
  version: 5.0
  ...
CAUSAL:
  algorithm: gfci
  alpha: 0.05
  penalty_discount: 1.0
  knowledge: prior.txt
  standardize_cols: true
  jitter: 0.001
```

### 4.2 Implement pipeline/parse.py

Port from cda_tools2's run_parse2.py (ParseData4 class):

- Config-driven data preparation pipeline
- All 25+ data operations: sort, recode, keep, drop, rename, add_lag, standardize, missing_value, etc.
- Global steps then per-case steps
- Prior file generation
- Case details CSV output

This is the largest porting effort. The ParseData4 class is ~1300 lines. Strategy:
- Keep the operation dispatch pattern (list of {op, arg} dicts)
- Clean up the code but preserve the config format for backwards compatibility
- Replace raw scripts with importable module

### 4.3 Implement pipeline/batch.py

Port from cda_tools2's run_causal2.py/run_causal3.py (CausalWrap/FastCDAWrap classes):

- Iterate over case CSV files in data directory
- Run causal discovery via `search.py` (using tetrad-port, not causal-cmd)
- Run SEM via `sem.py`
- Generate per-case outputs (edges, graphs, SEM estimates)
- Support --start/--end range for SLURM integration
- Support --list to enumerate cases

### 4.4 Implement pipeline/paths.py

Config-driven orchestration layer for effect size analysis. Ports the orchestration logic from cda_tools2's paths_plotdist2.py (PathsPlot class), while delegating actual drawing to `viz/plots.py` (Phase 3):

- Parse the `PATHS.effectsize` config section — iterate over destination variables, each with its `src` list, `title`, `grid` layout options, and optional `cases` filter
- Read `pathsdata.json` from the project output directory (contains per-case causal path effect sizes computed during batch run)
- For each destination variable, extract effect sizes for configured src/des pairs across all cases
- Call `viz/plots.py` functions to render heatmap grids with the config-specified layout (label sizes, dimensions, column/case reordering, rotation)
- Parse `PATHS.adjacency` config for adjacency matrix generation
- Parse `PATHS.check` config — count edge occurrences across cases (e.g., "how many subjects have panasneg --> binge?")
- Save all generated plots to the output directory

**Relationship to viz/plots.py:**
- `viz/plots.py` (Phase 3) = reusable plotting primitives (callable from notebooks or scripts)
- `pipeline/paths.py` (Phase 4) = reads config.yaml + pathsdata.json, then calls `viz/plots.py` to produce batch outputs

This separation means users can also call the heatmap functions directly in Jupyter without going through the config pipeline:
```python
from fastcausal.viz.plots import plot_effect_size_heatmap
plot_effect_size_heatmap(effect_data, src_vars=["panasneg", "panaspos"], des_var="binge", ...)
```

### 4.5 Implement pipeline/report.py

Port from cda_tools2's create_docx_proj.py:

- Collect PNG outputs from output directory
- Generate Word document with embedded images
- Multi-layout support (1wide, 2wide, 3wide)
- Include config, prior, case details as appendix

### 4.6 Implement pipeline/metrics.py

Port from cda_tools2's graphmetrics.py:

- Ancestor extraction
- Parent-child subgraph extraction
- Degree centrality
- Path computation

### 4.7 Implement io/wearables.py

Port from cda_tools2's fitbitdata.py and garmindata.py:

- Fitbit data integration (heart rate, sleep, stress)
- Garmin data integration
- Datetime merge operations

### 4.8 Implement cli.py

CLI entry points using click:

```python
import click

@click.group()
def main():
    """fastcausal - Causal Discovery Analysis tools."""
    pass

@main.command()
@click.option("--config", required=True, help="Path to config.yaml")
def parse(config):
    """Prepare and preprocess data."""

@main.command()
@click.option("--config", required=True)
@click.option("--start", default=0)
@click.option("--end", default=-1)
@click.option("--list", "list_cases", is_flag=True)
def run(config, start, end, list_cases):
    """Run causal discovery analysis."""

@main.command()
@click.option("--config", required=True)
def paths(config):
    """Compute path effect sizes."""

@main.command()
@click.option("--config", required=True)
@click.option("--mode", default="1wide")
@click.option("--stub", default="_label.png")
def report(config, mode, stub):
    """Generate analysis report document."""

@main.command()
@click.argument("datafile")
@click.option("--algorithm", default="gfci")
@click.option("--alpha", default=0.05)
@click.option("--output", default=".")
def analyze(datafile, algorithm, alpha, output):
    """Quick single-file causal analysis."""
```

### 4.9 Deliverable

- `fastcausal parse/run/paths/report` CLI commands work
- Existing config.yaml files from cda_tools2 projects are compatible
- SLURM batch workflows continue to work (just replace script names)

---

## Phase 5: Testing and Documentation ✅

### 5.1 Testing strategy

**Unit tests** (no external dependencies):
- `test_transform.py` — lag, standardize, subsample, jitter
- `test_edges.py` — edge parsing, extraction, selection
- `test_knowledge.py` — knowledge dict creation, prior file reading
- `test_sem.py` — lavaan conversion (SEM fitting needs semopy)
- `test_config.py` — YAML config parsing

**Integration tests** (require tetrad-port C++ extension):
- `test_search.py` — PC, FGES, GFCI execution
- `test_core.py` — full FastCausal workflow end-to-end

**Visualization tests** (require graphviz):
- `test_viz.py` — graph rendering, node styling, multi-graph

**CLI tests:**
- `test_cli.py` — click test runner for all commands

Port relevant tests from:
- fastcda's test_fastcda.py (37 tests) — mostly pure-Python, directly portable
- fastcda's test_integration.py (30 tests) — adapt to use tetrad-port instead of JPype
- tetrad-port's test_python_bindings.py — verify search results match

### 5.2 Documentation

- README.md with quickstart (5 lines to first graph)
- Migration guides:
  - `migration_from_fastcda.md` — API mapping table, before/after examples
  - `migration_from_cda_tools2.md` — CLI mapping, config.yaml changes
- Example notebooks:
  - `quickstart.ipynb` — minimal working example
  - `ema_analysis.ipynb` — full EMA workflow (replaces fastcda_demo_short)
  - `batch_project.ipynb` — config-driven batch analysis

### 5.3 Deliverable

- >90% test coverage on core modules
- All example notebooks run without errors
- Migration guides complete

---

## Phase 6: Publication and Deprecation

### 6.1 Publish fastcausal to PyPI

- Build and upload to PyPI
- Verify `pip install fastcausal` works on clean environments
- Verify `pip install fastcausal[all]` pulls in all optional dependencies

### 6.2 Deprecate fastcda

- Release fastcda 0.2.0 with deprecation warning in `__init__.py`:
  ```python
  import warnings
  warnings.warn(
      "fastcda is deprecated. Please use 'pip install fastcausal' instead. "
      "See migration guide at <url>",
      DeprecationWarning, stacklevel=2
  )
  ```
- Update fastcda README to point to fastcausal

### 6.3 Archive cda_tools2

- Update README to indicate scripts are superseded by fastcausal CLI
- No code changes needed (it was never a pip package)

### 6.4 Clean up tetrad-port

- Remove duplicated utility methods from tetrad-port's Python layer:
  - `edges_to_lavaan()` — now in fastcausal.sem
  - `run_semopy()` — now in fastcausal.sem
  - `add_lag_columns()` — now in fastcausal.transform
  - `standardize_df_cols()` — now in fastcausal.transform
  - `create_lag_knowledge()` — now in fastcausal.knowledge
- Keep tetrad-port focused on: algorithms + Knowledge + data validation
- Release tetrad-port 0.2.0 with trimmed Python API

Note: This cleanup should happen in a coordinated release. Users of tetrad-port standalone (if any) should be warned in advance via a minor version bump with deprecation warnings before removal.

---

## Utility Consolidation Map

This table shows where duplicated code across packages is consolidated in fastcausal:

| Utility | fastcda location | tetrad-port location | fastcausal target |
|---------|-----------------|---------------------|-------------------|
| `edges_to_lavaan()` | fastcda.py:1488 | `__init__.py`:277 | `sem.py` |
| `run_semopy()` | fastcda.py:1530 | `__init__.py`:323 | `sem.py` |
| `add_sem_results_to_graph()` | fastcda.py:1590 | — | `sem.py` |
| `add_lag_columns()` | fastcda.py:285 | `__init__.py`:373 | `transform.py` |
| `standardize_df_cols()` | fastcda.py:340 | `__init__.py`:413 | `transform.py` |
| `subsample_df()` | fastcda.py:370 | — | `transform.py` |
| `create_permuted_dfs()` | fastcda.py:400 | — | `transform.py` |
| `create_lag_knowledge()` | fastcda.py:470 | `__init__.py`:450 | `knowledge.py` |
| `load_knowledge()` | fastcda.py:430 | — | `knowledge.py` |
| `read_prior_file()` | fastcda.py:500 | — | `knowledge.py` |
| `extract_edges()` | fastcda.py:1470 | — | `edges.py` |
| `select_edges()` | fastcda.py:1680 | — | `edges.py` |
| `resolve_node_styles()` | fastcda.py:965 | — | `viz/styling.py` |
| `show_styled_graph()` | fastcda.py:1104 | — | `viz/graphs.py` |
| `show_n_graphs()` | fastcda.py:1200 | — | `viz/graphs.py` |
| `_parse_edges_to_graph_info()` | — | `__init__.py`:495 | `edges.py` |

---

## Config.yaml Compatibility

fastcausal will support cda_tools2's v4.0 config format with these changes:

### Sections preserved as-is
- `GLOBAL` — directories, name, title, header, cases_ignore
- `PREP` — datafile, variables, steps_global, steps_case (all 25+ operations)
- `SEM` — plotting options, include_model_edges
- `GRAPHS` — graphviz settings, ancestors, parentchild, save_plot operations
- `PATHS` — effectsize, adjacency, check configurations

### Section updated
- `CAUSAL` — simplified, Java-specific fields ignored:

```yaml
# v5.0 format (new):
CAUSAL:
  algorithm: gfci           # pc, fges, gfci
  alpha: 0.05
  penalty_discount: 1.0
  depth: -1                 # new: exposed for PC/GFCI
  max_degree: -1             # new: exposed for FGES/GFCI
  knowledge: prior.txt
  standardize_cols: true
  jitter: 0.001
```

```yaml
# v4.0 format (legacy, accepted with deprecation warning):
# Java-specific fields (causal-cmd, cmdpath, version, jarautopath) are parsed but ignored.
CAUSAL:
  causal-cmd:
    algorithm: gfci
    alpha: 0.05
    penaltyDiscount: 1.0
    cmdpath: /Users/kolim/bin
    version: 1.11.1
    ...
```

The config parser checks `GLOBAL.version`. If `4.0`, it emits a deprecation warning and maps the old `causal-cmd` sub-key format to the new flat format internally. If `5.0`, it uses the new format directly.

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| **tetrad-port wheel builds fail on some platforms** | Users can't install without C++ compiler | Provide sdist fallback + clear error message with build instructions. Target the 3 most common platforms first. |
| **Algorithm output differences vs Java Tetrad** | Users get different results than fastcda | tetrad-port already has golden-master tests. Add comparison tests against known fastcda outputs on bundled datasets. |
| **cda_tools2 config.yaml edge cases** | Old projects break with new parser | Full backwards-compatibility testing with existing proj_* folders. Keep old field names parsed even if unused. |
| **dgraph_flex API changes** | Version mismatch breaks visualization | Pin minimum version in dependencies. dgraph_flex is stable (0.1.11). |
| **Large porting effort for run_parse2.py** | Phase 4 takes longer than expected | run_parse2.py is the largest single file (~1300 lines). Consider initially wrapping it rather than rewriting. |
| **semopy version incompatibilities** | SEM results differ across versions | Pin semopy>=2.3 and add version check at runtime. |
| **Loss of BOSS algorithm** | cda_tools2 supports BOSS via causal-cmd | tetrad-port roadmap includes BOSS. Can be added as tetrad-port is extended. |

---

## Summary of Effort by Phase

| Phase | Estimated Scope | Key Deliverable |
|-------|----------------|-----------------|
| **Phase 1: Foundation** | Small | tetrad-port on PyPI, fastcausal skeleton |
| **Phase 2: Core API** | Medium | FastCausal class, interactive Jupyter workflows |
| **Phase 3: Visualization** | Medium | Node styling, multi-graph, all graph rendering |
| **Phase 4: Batch/CLI** | Large | Config-driven batch, CLI commands, report generation |
| **Phase 5: Testing/Docs** | Medium | Test suite, notebooks, migration guides |
| **Phase 6: Publish** | Small | PyPI release, deprecation notices |

Phases 1-2 are the critical path. Once those are complete, fastcausal is usable for interactive work (the most common use case). Phases 3-4 can proceed in parallel.
