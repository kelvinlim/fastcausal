# CLAUDE.md - fastcausal

## Project Overview

fastcausal is a unified Python package for causal discovery analysis, combining:
- **tetrad-port** (C++ causal algorithms via nanobind — no Java required)
- **dgraph_flex** (graph data structure and Graphviz rendering)
- Interactive Jupyter notebook support
- Config-driven batch processing pipeline (from cda_tools2)

## Architecture

```
fastcausal  (this package — user-facing API + CLI)
   ├── tetrad-port  (dependency — C++ algorithms: PC, FGES, GFCI, BOSS, BOSS-FCI, GRaSP, GRaSP-FCI)
   └── dgraph_flex  (dependency — graph rendering)
```

## Package Structure

- `core.py` — FastCausal class (main user-facing API)
- `search.py` — thin wrapper around tetrad-port algorithms
- `sem.py` — SEM fitting via semopy
- `transform.py` — lag columns, standardization, subsampling, jitter
- `knowledge.py` — prior knowledge handling
- `edges.py` — edge parsing, extraction, graph building
- `cli.py` — click-based CLI entry points
- `viz/` — visualization (styling, graphs, plots)
- `pipeline/` — batch processing (config, parse, batch, paths, report, metrics)
- `io/` — data loading, wearable device data

## Build & Test

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

## Conventions

- Python >= 3.11
- Version is in both `fastcausal/__init__.py` and `pyproject.toml` — keep in sync
- CLI uses click framework
- `knowledge` parameter defaults to `None` (no auto-detection)
- Config.yaml v5.0 is the current format; v4.0 accepted with deprecation warning
- Edge types: `-->`, `o->`, `o-o`, `<->`, `---` (Tetrad conventions)
- SEM includes both `-->` and `o->` edges by default

## Key Design Decisions

- No Java dependency — all algorithms run via tetrad-port C++ bindings
- DgraphFlex is the graph data structure throughout (not networkx)
- FastCausal class delegates to focused modules (search, sem, transform, etc.)
- Lazy imports used in FastCausal methods to keep import time fast
- Bundled sample data in fastcausal/data/

## Related Repositories

- tetrad-port: /home/kolim/Projects/tetrad-port/
- dgraph_flex: /home/kolim/Projects/dgraph_flex/
- fastcda: /home/kolim/Projects/fastcda/ (being deprecated)
- cda_tools2: /home/kolim/Projects/cda_tools2/ (being archived)
