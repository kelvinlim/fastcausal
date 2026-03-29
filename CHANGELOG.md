# Changelog

All notable changes to fastcausal are documented in this file.

## [0.1.5] - 2026-03-29

### Fixed
- **README images on PyPI** — use absolute GitHub raw URLs so graph images render on pypi.org (not just on GitHub)

## [0.1.4] - 2026-03-29

### Added
- **`fastcausal init` CLI command** — generates a sample `config.yaml` with commented examples of all available parameters and parse operations
- **`fastcausal_demo_short.ipynb`** — interactive demo notebook (equivalent to the fastcda demo), with executed outputs viewable on GitHub
- **MkDocs documentation site** — deployed at https://kelvinlim.github.io/fastcausal/ with Material theme, API reference (mkdocstrings), and Jupyter tutorial support (mkdocs-jupyter)
- **README graph images** — quickstart and styled graph PNGs embedded in README so results are visible directly on GitHub
- **`docs` optional dependency group** — `pip install fastcausal[docs]` for mkdocs-material, mkdocstrings, mkdocs-jupyter

### Fixed
- **SEM solver convergence** — exclude bidirectional (`<->`) and undirected (`---`) edges from SEM model by default. PAG algorithms use these to indicate possible latent confounding, which cannot be properly represented as simple covariances in semopy and caused SLSQP solver failures. Added `include_covariances` parameter to `edges_to_lavaan()` for opt-in
- **CLI `--version`** — now reads from `__version__` in `__init__.py` instead of stale package metadata
- **Build excludes** — added excludes for linked codebases so `dist` builds work correctly

### Changed
- **README Quick Start** — consolidated Quick Start and Interactive Workflow sections; uses standardized boston dataset with explicit temporal knowledge dictionary and SEM edge weights

## [0.1.3] - 2026-03-08

### Changed
- Updated dependencies

## [0.1.2] - 2026-03-08

### Changed
- Made `set_tier_forbidden_within` opt-in per tier

## [0.1.1] - 2026-03-08

### Added
- Tutorials, example notebooks, and migration docs
- Comprehensive README with usage examples

## [0.1.0] - 2026-03-07

### Added
- Initial release
- FastCausal class with unified API for causal discovery
- Seven algorithms: PC, FGES, GFCI, BOSS, BOSS-FCI, GRaSP, GRaSP-FCI
- SEM fitting via semopy
- Data transforms: lag columns, standardization, subsampling
- Prior knowledge support (temporal tiers, forbidden/required edges)
- Bootstrapped stability analysis
- Graph visualization with fnmatch-based node styling
- Multi-graph comparison with shared node layouts
- Config-driven batch processing pipeline
- Click-based CLI (parse, run, paths, report, analyze)
- Bundled sample EMA dataset
