# fastcausal

**fastcausal** is a Python package for causal discovery analysis. It provides a unified API for running state-of-the-art causal search algorithms, fitting structural equation models, and visualizing causal graphs — with **no Java required**.

---

## Key Features

- **Seven algorithms**: PC, FGES, GFCI, BOSS, BOSS-FCI, GRaSP, GRaSP-FCI
- **No Java**: algorithms run via [tetrad-port](https://github.com/kelvinlim/tetrad-port) (C++ nanobind bindings)
- **Prior knowledge**: temporal tiers, forbidden/required edges
- **Stability search**: bootstrap-based robust edge discovery
- **SEM fitting**: structural equation models via semopy
- **Interactive**: designed for Jupyter notebooks

---

## Prerequisites

- **Python 3.11+**
- **Graphviz** (`dot` must be on PATH) — [download](https://graphviz.org/download/)

No Java installation needed.

---

## Installation

```bash
pip install fastcausal
```

All features — SEM fitting (semopy), Jupyter/matplotlib/seaborn support, and
Word report generation — are included by default.

### Conda install (Miniforge3 recommended)

For reproducible environments, use the repository's `environment.yml`:

1. Install Miniforge3 (conda-forge based):

- Windows (PowerShell via winget):

```powershell
winget install --id CondaForge.Miniforge3 -e
```

- macOS/Linux installers:
    https://github.com/conda-forge/miniforge/releases/latest

2. Create and activate the environment:

```bash
conda env create -f environment.yml
conda activate fastcausal_env
```

     This environment installs both `fastcausal` and Graphviz binaries needed to render causal graphs.

3. (Optional) verify installation:

```bash
python -c "import fastcausal; print(fastcausal.__version__)"
dot -V
```

---

## Quick Start

```python
from fastcausal import FastCausal

fc = FastCausal()

# Load the built-in EMA dataset
df = fc.load_sample("boston")

# Add lagged columns and standardize
df = fc.add_lag_columns(df)
df = fc.standardize(df)

# Create temporal prior knowledge (lag vars in tier 0, current in tier 1)
knowledge = fc.create_lag_knowledge(df.columns)

# Run GFCI causal search
results, graph = fc.run_search(
    df,
    algorithm="gfci",
    alpha=0.01,
    penalty_discount=1.0,
    knowledge=knowledge,
)

# Display the graph (in a Jupyter notebook)
fc.show_graph(graph)
```

---

## Platforms

Tested on **Windows 11**, **macOS Sequoia**, and **Ubuntu 24.04**.

---

## Tutorials

- [Quick Start](tutorials/quickstart.ipynb) — minimal 5-step workflow
- [EMA Analysis](tutorials/ema_analysis.ipynb) — full ecological momentary assessment workflow with node styling, multi-graph comparison, stability search, and SEM
