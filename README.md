# fastcausal

Fast, easy-to-use causal discovery analysis tools for Python.

[![PyPI version](https://badge.fury.io/py/fastcausal.svg)](https://pypi.org/project/fastcausal/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

**fastcausal** provides a unified Python interface for causal discovery analysis, combining the functionality of several earlier packages into one pip-installable tool. It supports both interactive Jupyter notebook workflows and config-driven batch processing of large datasets.

Key features:

- **No Java dependency** — uses [tetrad-port](https://github.com/kelvinlim/tetrad-port) (C++ port of Tetrad algorithms) instead of Java
- **Three causal discovery algorithms** — PC, FGES, GFCI
- **Prior knowledge support** — temporal tiers, forbidden/required edges
- **Bootstrapped stability analysis** — edge frequency selection across subsampled runs
- **SEM fitting** — automatic structural equation modeling via semopy
- **Flexible graph visualization** — node styling with fnmatch patterns, multi-graph comparison with shared layouts
- **Batch pipeline** — config-driven processing of hundreds of cases via CLI
- **Report generation** — automated Word document reports with embedded graphs

## Installation

```bash
pip install fastcausal            # core package
pip install fastcausal[sem]       # + SEM fitting (semopy)
pip install fastcausal[jupyter]   # + Jupyter/matplotlib/seaborn
pip install fastcausal[batch]     # + Word report generation
pip install fastcausal[all]       # everything
```

## Quick Start

```python
from fastcausal import FastCausal

fc = FastCausal()

# Load data
df = fc.load_sample("boston")

# Run causal discovery
results, graph = fc.run_search(df, algorithm="gfci", alpha=0.05)

# View the graph
fc.show_graph(graph)

# Save to file
fc.save_graph(graph, "my_result", plot_format="png")
```

## Interactive Workflow

```python
from fastcausal import FastCausal

fc = FastCausal()
df = fc.load_csv("my_data.csv")

# Add lagged columns for time-series analysis
df = fc.add_lag_columns(df)
df = fc.standardize(df)

# Create temporal prior knowledge
knowledge = fc.create_lag_knowledge(df.columns)

# Run stability analysis (bootstrapped)
results, graph = fc.run_stability(
    df,
    algorithm="gfci",
    knowledge=knowledge,
    runs=100,
    min_fraction=0.75,
)

# Visualize with custom node styles
fc.show_graph(graph, node_styles=[
    {"pattern": "*_lag", "shape": "box", "fillcolor": "lightyellow"},
    {"pattern": "PANAS_*", "fillcolor": "lightblue"},
])
```

## CLI Usage

fastcausal provides a command-line interface for batch processing:

```bash
# Data preparation
fastcausal parse --config proj/config.yaml

# Batch causal discovery across cases
fastcausal run --config proj/config.yaml
fastcausal run --config proj/config.yaml --start 0 --end 50
fastcausal run --config proj/config.yaml --list

# Effect size analysis and heatmaps
fastcausal paths --config proj/config.yaml

# Generate Word report
fastcausal report --config proj/config.yaml --mode 2wide

# Quick single-file analysis
fastcausal analyze data.csv --algorithm gfci --output results/
```

## Supported Algorithms

| Algorithm | Description | Key Parameters |
|-----------|-------------|----------------|
| **PC** | Constraint-based, uses conditional independence tests | `alpha` |
| **FGES** | Score-based, greedy search with BIC scoring | `penalty_discount` |
| **GFCI** | Hybrid constraint + score-based | `alpha`, `penalty_discount` |

## Architecture

fastcausal consolidates four earlier codebases into a layered architecture:

```
pip install fastcausal
        |
    fastcausal  (API + CLI + viz + SEM + batch)
   /          \
tetrad-port    dgraph_flex
(C++ algorithms) (graph rendering)
```

- **tetrad-port** — C++ port of CMU Tetrad algorithms, exposed via nanobind
- **dgraph_flex** — Graphviz-based directed graph rendering

## Project Structure

```
fastcausal/
├── core.py              # FastCausal class (main API)
├── search.py            # Algorithm wrapper (PC, FGES, GFCI)
├── sem.py               # SEM fitting via semopy
├── transform.py         # Lag columns, standardization, subsampling
├── knowledge.py         # Prior knowledge handling
├── edges.py             # Edge parsing, selection, deduplication
├── cli.py               # Click-based CLI
├── viz/
│   ├── styling.py       # fnmatch-based node styling
│   ├── graphs.py        # Graph display and save (single + multi)
│   └── plots.py         # Heatmaps and effect size plots
├── pipeline/
│   ├── config.py        # YAML config parsing (v4.0 + v5.0)
│   ├── parse.py         # Data preparation engine
│   ├── batch.py         # Batch causal discovery
│   ├── paths.py         # Effect size analysis
│   ├── report.py        # Word document generation
│   └── metrics.py       # Graph metrics (centrality, ancestors)
└── io/
    ├── data.py           # CSV loading, sample datasets
    └── wearables.py      # Fitbit/Garmin integration (planned)
```

## Documentation

- [Consolidation Plan](ConsolidationPlan.md) — Implementation plan and phase status
- [Consolidation Recommendation](ConsolidationRecommendation.md) — Architecture decision record
- [Project Conventions](CLAUDE.md) — Development guidelines and conventions

## Config File Format

fastcausal uses YAML config files for batch processing. Version 5.0 is the current format; version 4.0 (from cda_tools2) is accepted with a deprecation warning.

```yaml
GLOBAL:
  version: 5.0
  name: my_project
  title: "My Causal Analysis"

CAUSAL:
  algorithm: gfci
  alpha: 0.05
  penalty_discount: 1.0
  knowledge: prior.txt
  standardize_cols: true
```

## Requirements

- Python >= 3.11
- [tetrad-port](https://github.com/kelvinlim/tetrad-port) >= 0.1.0
- [dgraph_flex](https://github.com/kelvinlim/dgraph_flex) >= 0.1.11
- [Graphviz](https://graphviz.org/) (system install for graph rendering)

## License

MIT

## Citation

If you use fastcausal in your research, please cite the relevant algorithm papers and this package.
