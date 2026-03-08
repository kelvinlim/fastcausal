# Migrating from cda_tools2 to fastcausal

cda_tools2 was a collection of standalone Python scripts for config-driven batch causal discovery. fastcausal replaces those scripts with installable CLI commands and importable modules.

## CLI command mapping

| cda_tools2 script | fastcausal CLI | Notes |
|-------------------|---------------|-------|
| `python run_parse2.py --config config.yaml` | `fastcausal parse --config config.yaml` | Data preparation |
| `python run_causal2.py --config config.yaml` | `fastcausal run --config config.yaml` | Batch causal discovery |
| `python run_causal3.py --config config.yaml --start 0 --end 85` | `fastcausal run --config config.yaml --start 0 --end 85` | Partial batch (SLURM) |
| `python run_causal2.py --config config.yaml --list` | `fastcausal run --config config.yaml --list` | List cases |
| `python paths_plotdist2.py --config config.yaml` | `fastcausal paths --config config.yaml` | Effect size plots |
| `python create_docx_proj.py --config config.yaml --mode 2wide --stub _label.png` | `fastcausal report --config config.yaml --mode 2wide --stub _label.png` | Word report |

## Config.yaml changes (v4.0 → v5.0)

fastcausal introduces **v5.0** config format. v4.0 configs are accepted with a deprecation warning.

The only section that changes is `CAUSAL`. All other sections (`GLOBAL`, `PREP`, `SEM`, `GRAPHS`, `PATHS`) are unchanged.

### CAUSAL section

```yaml
# v4.0 (old — still works, with deprecation warning)
GLOBAL:
  version: 4.0
  ...
CAUSAL:
  causal-cmd:
    algorithm: gfci
    alpha: 0.05
    penaltyDiscount: 1.0
    cmdpath: /Users/kolim/bin
    version: 1.11.1
    jarautopath: true
    knowledge: prior.txt
    standardize_cols: true
    jitter: 0.001
```

```yaml
# v5.0 (new — preferred)
GLOBAL:
  version: 5.0
  ...
CAUSAL:
  algorithm: gfci         # pc, fges, gfci
  alpha: 0.05
  penalty_discount: 1.0   # note: underscore, not camelCase
  depth: -1               # optional; -1 = unlimited
  max_degree: -1          # optional; -1 = unlimited
  knowledge: prior.txt
  standardize_cols: true
  jitter: 0.001
```

**Fields removed** (Java-specific, silently ignored in v4.0 mode):
- `cmdpath` — no longer needed (no Java runtime)
- `version` — causal-cmd version
- `jarautopath` — Java path discovery

**Fields renamed** in v5.0:
- `penaltyDiscount` → `penalty_discount`

## No Java required

cda_tools2 used causal-cmd (a Java JAR) to run algorithms. fastcausal uses tetrad-port (C++ bindings), so no Java installation is needed.

```bash
# Old: required Java + causal-cmd JAR
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
python run_causal2.py --config config.yaml

# New: just Python
fastcausal run --config config.yaml
```

## SLURM batch workflows

The `--start` and `--end` arguments work identically:

```bash
# Old
for i in $(seq 0 10 84); do
    sbatch --wrap="python run_causal3.py --config config.yaml --start $i --end $((i+9))"
done

# New
for i in $(seq 0 10 84); do
    sbatch --wrap="fastcausal run --config config.yaml --start $i --end $((i+9))"
done
```

## Using fastcausal as a library

The pipeline modules are fully importable for use in scripts or notebooks:

```python
from fastcausal.pipeline.config import load_config
from fastcausal.pipeline.parse import ParseData
from fastcausal.pipeline.batch import run_batch
from fastcausal.pipeline.paths import run_paths
from fastcausal.pipeline.report import generate_report

# Load and validate config
cfg = load_config("proj_ema/config.yaml")

# Run steps programmatically
parse_data = ParseData(cfg)
parse_data.run()

run_batch(cfg)
run_paths(cfg)
generate_report(cfg, mode="2wide")
```

## Quick single-file analysis (new)

fastcausal adds a convenience command for one-off analysis that doesn't need a full config.yaml:

```bash
fastcausal analyze data.csv --algorithm gfci --alpha 0.05 --output results/
```

## Algorithm support

| Algorithm | cda_tools2 | fastcausal |
|-----------|-----------|------------|
| PC | ✓ (via causal-cmd) | ✓ (C++) |
| FGES | ✓ (via causal-cmd) | ✓ (C++) |
| GFCI | ✓ (via causal-cmd) | ✓ (C++) |
| BOSS | ✓ (via causal-cmd) | Planned |

## Output file compatibility

All output files have the same names and formats as cda_tools2:
- `pathsdata.json` — per-case effect sizes
- `case_details.csv` — case metadata
- `*_edges.txt` — edge lists
- `*_label.png` — graph images

Existing downstream scripts that read these files require no changes.
