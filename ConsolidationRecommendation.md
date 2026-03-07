# Consolidation Recommendation for fastcausal

## Current Landscape

| Package | Role | Key Strength | Key Limitation |
|---------|------|-------------|----------------|
| **tetrad-port** | Causal algorithms (C++) | No Java dependency, fast | No visualization, limited API |
| **fastcda** | Interactive analysis (Python) | Best graphing, Jupyter UX | Requires Java (JPype + Tetrad JAR) |
| **dgraph_flex** | Graph data structure + rendering | Clean edge model, Graphviz | Standalone utility, not end-user tool |
| **cda_tools2** | Batch processing pipeline | Config-driven, report generation | Old scripts, not a package, Java dep |

Notable overlap: `fastcda` and `tetrad-port` both implement `edges_to_lavaan()`, `run_semopy()`, `add_lag_columns()`, `standardize_df_cols()`, and `create_lag_knowledge()`.

## Goals

1. Fast, easy install (`pip install`) package for causal analyses
2. Command-line processing for batch workflows (hundreds of cases)
3. Interactive Jupyter notebook support for teaching and exploration
4. Elimination of the Java dependency
5. Ease of use modeled on the R graphicalVAR package

---

## Approaches Considered

### Approach A: Layered Packages (Recommended)

Three pip-installable packages with clear dependency flow:

```
dgraph_flex  (visualization layer - keep as-is)
     ^
tetrad-port  (computation layer - keep as-is)
     ^
fastcausal   (NEW unified API + CLI layer)
```

`pip install fastcausal` pulls in `tetrad-port` and `dgraph_flex` automatically.

**What goes where:**

- **dgraph_flex** - Unchanged. Graph data structure, edge types, Graphviz rendering.
- **tetrad-port** - Unchanged. C++ algorithms (PC, FGES, GFCI), Python bindings, no Java.
- **fastcausal** (new) - The user-facing package:
  - High-level `FastCausal` class modeled on graphicalVAR's simplicity
  - Absorbs fastcda's API patterns (run_model_search, run_stability_search, node styling, multi-graph comparison)
  - Absorbs cda_tools2's batch processing (config.yaml pipeline, data prep, report generation) as CLI entry points
  - SEM integration (semopy), lag columns, standardization, prior knowledge consolidated here

**User experience:**

```python
# Interactive (Jupyter)
from fastcausal import FastCausal
fc = FastCausal()
df = fc.load_data("my_data.csv")
results, graph = fc.run_gfci(df, alpha=0.05, penalty_discount=1.0)
fc.show_graph(graph, node_styles=[...])
```

```bash
# Batch (CLI)
fastcausal parse  --config proj_ema/config.yaml
fastcausal run    --config proj_ema/config.yaml --start 0 --end 85
fastcausal report --config proj_ema/config.yaml --mode 2wide
```

**Pros:**
- Users install one thing: `pip install fastcausal`
- Clean separation of concerns - algorithms, visualization, and user API are independent
- `dgraph_flex` and `tetrad-port` remain useful standalone for advanced users
- Easiest migration path - existing repos stay intact, new package composes them
- `tetrad-port` can publish pre-built wheels independently (the hard compilation step)
- Matches the graphicalVAR model: simple top-level API, complexity hidden underneath

**Cons:**
- Three packages to maintain and version-coordinate
- Users who `pip install tetrad-port` alone need to know about `fastcausal` for the full experience
- Pre-built wheels for tetrad-port (C++ extension) require CI/CD setup with cibuildwheel

---

### Approach B: Single Monolithic Package

Merge all four codebases into one repository and one `pip install fastcausal`.

```
fastcausal/
  src/           # C++ (from tetrad-port)
  bindings/      # nanobind (from tetrad-port)
  fastcausal/
    core/        # algorithms API
    graph/       # dgraph_flex absorbed
    viz/         # node styling, multi-graph (from fastcda)
    pipeline/    # batch processing (from cda_tools2)
    api.py       # high-level FastCausal class
  CMakeLists.txt
  pyproject.toml
```

**Pros:**
- Single repo, single version, single install
- No cross-package version coordination
- Easier to refactor across boundaries

**Cons:**
- Hardest migration - must merge four repos and resolve all conflicts
- dgraph_flex loses its independence (useful beyond causal analysis)
- C++ build complexity contaminates whole package - if C++ build breaks, nothing installs
- Larger package, longer installs
- Breaking changes in one area force a full package release

---

### Approach C: Extended tetrad-port

Expand tetrad-port to become the unified package, absorbing all functionality.

**Pros:**
- tetrad-port already has the hardest piece (C++ + Python bindings) working
- Natural evolution of existing codebase

**Cons:**
- Mixes concerns - a low-level algorithm library shouldn't own visualization and batch processing
- Package name implies a port, not a user-friendly tool
- Violates single-responsibility principle

---

### Approach D: Thin Facade Only

Keep all four repos unchanged. Create a tiny `fastcausal` that just imports and re-exports.

**Pros:**
- Minimal new code
- Nothing changes in existing repos

**Cons:**
- Doesn't consolidate duplicated utility code
- cda_tools2 remains unpackaged scripts
- fastcda continues to require Java - the Java elimination goal isn't met
- Users confused by five related packages

---

## Recommendation: Approach A (Layered Packages)

### Why This Approach

1. **Achieves all three goals:**
   - Command-line processing: `fastcausal` CLI absorbs cda_tools2 pipeline
   - Interactive Jupyter: `fastcausal` API absorbs fastcda's UX patterns
   - No Java: `tetrad-port` C++ backend replaces JPype/Tetrad JAR

2. **Migration is incremental:** Existing repos stay intact. `dgraph_flex` and `tetrad-port` continue working as-is. `fastcausal` is additive.

3. **C++ build problem is isolated:** Pre-built wheels for `tetrad-port` can be published to PyPI via cibuildwheel. If a user's platform isn't supported, only that dependency fails.

4. **Matches successful precedents:** This is how scikit-learn (depends on scipy, numpy), plotly (depends on plotly.js), and similar packages work.

### Migration Steps

1. **Publish `tetrad-port` to PyPI** with pre-built wheels (cibuildwheel for Linux/macOS/Windows)
2. **Create `fastcausal` repo** with `FastCausal` class, porting fastcda's API to use tetrad-port instead of JPype
3. **Port cda_tools2 batch logic** into `fastcausal` as CLI commands (using click or argparse)
4. **Consolidate duplicated utilities** (SEM, lag, lavaan, standardization) into `fastcausal`, remove from tetrad-port's Python layer
5. **Port fastcda's visualization** (node styling, multi-graph, stability search) into `fastcausal`
6. **Deprecate `fastcda`** - it becomes unnecessary once `fastcausal` covers its functionality without Java
7. **Archive `cda_tools2`** - its functionality lives in `fastcausal` CLI

### Final Package Dependency Graph

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
