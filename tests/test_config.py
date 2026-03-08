"""Tests for fastcausal.pipeline.config — YAML config parsing and migration."""

import os
import warnings

import pytest
import yaml

from fastcausal.pipeline.config import (
    load_config,
    get_project_dir,
    get_data_dir,
    get_output_dir,
    get_raw_data_dir,
    get_causal_params,
    get_sem_params,
)


def _write_config(tmp_path, cfg_dict):
    """Write a config dict to a YAML file and return the path."""
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(cfg_dict, f)
    return str(config_path)


class TestLoadConfigV5:
    def test_basic_v5(self, tmp_path):
        cfg_dict = {
            "GLOBAL": {"version": 5.0, "name": "test_project"},
            "CAUSAL": {"algorithm": "gfci", "alpha": 0.01},
        }
        cfg = load_config(_write_config(tmp_path, cfg_dict))
        assert cfg["GLOBAL"]["version"] == 5.0
        assert cfg["CAUSAL"]["algorithm"] == "gfci"

    def test_project_dir_set(self, tmp_path):
        cfg_dict = {"GLOBAL": {"version": 5.0}}
        cfg = load_config(_write_config(tmp_path, cfg_dict))
        assert cfg["_project_dir"] == str(tmp_path)

    def test_config_path_set(self, tmp_path):
        cfg_dict = {"GLOBAL": {"version": 5.0}}
        config_path = _write_config(tmp_path, cfg_dict)
        cfg = load_config(config_path)
        assert cfg["_config_path"] == os.path.abspath(config_path)

    def test_missing_global_raises(self, tmp_path):
        cfg_dict = {"CAUSAL": {"algorithm": "pc"}}
        with pytest.raises(ValueError, match="GLOBAL"):
            load_config(_write_config(tmp_path, cfg_dict))


class TestLoadConfigV4Migration:
    def test_v4_deprecation_warning(self, tmp_path):
        cfg_dict = {
            "GLOBAL": {"version": 4.0},
            "CAUSAL": {
                "causal-cmd": {
                    "algorithm": "gfci",
                    "alpha": 0.05,
                    "penaltyDiscount": 2.0,
                }
            },
        }
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cfg = load_config(_write_config(tmp_path, cfg_dict))
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()

    def test_v4_migration_maps_fields(self, tmp_path):
        cfg_dict = {
            "GLOBAL": {"version": 4.0},
            "CAUSAL": {
                "causal-cmd": {
                    "algorithm": "fges",
                    "alpha": 0.01,
                    "penaltyDiscount": 3.0,
                    "knowledge": "prior.txt",
                }
            },
        }
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cfg = load_config(_write_config(tmp_path, cfg_dict))

        assert cfg["CAUSAL"]["algorithm"] == "fges"
        assert cfg["CAUSAL"]["alpha"] == 0.01
        assert cfg["CAUSAL"]["penalty_discount"] == 3.0
        assert cfg["CAUSAL"]["knowledge"] == "prior.txt"

    def test_v4_default_version_treated_as_legacy(self, tmp_path):
        """Config without version should be treated as v4."""
        cfg_dict = {
            "GLOBAL": {"name": "old_project"},
            "CAUSAL": {"causal-cmd": {"algorithm": "pc"}},
        }
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cfg = load_config(_write_config(tmp_path, cfg_dict))
            assert len(w) == 1
            assert cfg["CAUSAL"]["algorithm"] == "pc"


class TestGetDirectories:
    def test_default_dirs(self, tmp_path):
        cfg_dict = {"GLOBAL": {"version": 5.0}}
        cfg = load_config(_write_config(tmp_path, cfg_dict))

        assert get_project_dir(cfg) == str(tmp_path)
        assert get_data_dir(cfg) == os.path.join(str(tmp_path), "data")
        assert get_raw_data_dir(cfg) == os.path.join(str(tmp_path), "data_raw")

    def test_custom_dirs(self, tmp_path):
        cfg_dict = {
            "GLOBAL": {
                "version": 5.0,
                "directories": {
                    "datadir": "my_data",
                    "output": "my_output",
                    "rawdatadir": "my_raw",
                },
            },
        }
        cfg = load_config(_write_config(tmp_path, cfg_dict))
        assert get_data_dir(cfg).endswith("my_data")
        assert get_output_dir(cfg).endswith("my_output")
        assert get_raw_data_dir(cfg).endswith("my_raw")

    def test_output_from_causal_out(self, tmp_path):
        cfg_dict = {
            "GLOBAL": {"version": 5.0},
            "CAUSAL": {"out": "causal_output"},
        }
        cfg = load_config(_write_config(tmp_path, cfg_dict))
        assert get_output_dir(cfg).endswith("causal_output")


class TestGetCausalParams:
    def test_defaults(self, tmp_path):
        cfg_dict = {"GLOBAL": {"version": 5.0}}
        cfg = load_config(_write_config(tmp_path, cfg_dict))
        params = get_causal_params(cfg)
        assert params["algorithm"] == "gfci"
        assert params["alpha"] == 0.05
        assert params["penalty_discount"] == 1.0
        assert params["depth"] == -1
        assert params["standardize_cols"] is True
        assert params["jitter"] == 0.0

    def test_custom_params(self, tmp_path):
        cfg_dict = {
            "GLOBAL": {"version": 5.0},
            "CAUSAL": {
                "algorithm": "pc",
                "alpha": 0.01,
                "penalty_discount": 2.0,
                "depth": 3,
                "jitter": 0.001,
            },
        }
        cfg = load_config(_write_config(tmp_path, cfg_dict))
        params = get_causal_params(cfg)
        assert params["algorithm"] == "pc"
        assert params["alpha"] == 0.01
        assert params["penalty_discount"] == 2.0
        assert params["depth"] == 3
        assert params["jitter"] == 0.001


class TestGetSemParams:
    def test_defaults(self, tmp_path):
        cfg_dict = {"GLOBAL": {"version": 5.0}}
        cfg = load_config(_write_config(tmp_path, cfg_dict))
        params = get_sem_params(cfg)
        assert "include_types" in params
        assert "-->" in params["include_types"]
        assert "o->" in params["include_types"]

    def test_custom_sem(self, tmp_path):
        cfg_dict = {
            "GLOBAL": {"version": 5.0},
            "SEM": {
                "plotting": {"fontname": "Arial", "min_pvalue": 0.05},
                "include_model_edges": [["-->", "~"]],
            },
        }
        cfg = load_config(_write_config(tmp_path, cfg_dict))
        params = get_sem_params(cfg)
        assert params["fontname"] == "Arial"
        assert params["min_pvalue"] == 0.05
        assert params["include_types"] == ["-->"]
