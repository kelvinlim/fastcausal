"""Tests for fastcausal.cli — CLI command integration tests."""

import os

import pytest
import yaml
from click.testing import CliRunner

from fastcausal.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestCLIHelp:
    def test_main_help(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "fastcausal" in result.output

    def test_parse_help(self, runner):
        result = runner.invoke(main, ["parse", "--help"])
        assert result.exit_code == 0
        assert "--config" in result.output

    def test_run_help(self, runner):
        result = runner.invoke(main, ["run", "--help"])
        assert result.exit_code == 0
        assert "--start" in result.output
        assert "--end" in result.output

    def test_paths_help(self, runner):
        result = runner.invoke(main, ["paths", "--help"])
        assert result.exit_code == 0

    def test_report_help(self, runner):
        result = runner.invoke(main, ["report", "--help"])
        assert result.exit_code == 0
        assert "--mode" in result.output
        assert "--stub" in result.output

    def test_analyze_help(self, runner):
        result = runner.invoke(main, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "--algorithm" in result.output


class TestCLIVersion:
    def test_version(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestCLIConfigRequired:
    def test_parse_requires_config(self, runner):
        result = runner.invoke(main, ["parse"])
        assert result.exit_code != 0

    def test_run_requires_config(self, runner):
        result = runner.invoke(main, ["run"])
        assert result.exit_code != 0

    def test_paths_requires_config(self, runner):
        result = runner.invoke(main, ["paths"])
        assert result.exit_code != 0

    def test_report_requires_config(self, runner):
        result = runner.invoke(main, ["report"])
        assert result.exit_code != 0


class TestCLIAnalyze:
    def test_analyze_with_csv(self, runner, tmp_path):
        """Test analyze command with a real CSV file."""
        import numpy as np
        import pandas as pd

        np.random.seed(42)
        n = 100
        df = pd.DataFrame({
            "X": np.random.randn(n),
            "Y": np.random.randn(n),
            "Z": np.random.randn(n),
        })
        csv_path = str(tmp_path / "test_data.csv")
        df.to_csv(csv_path, index=False)

        result = runner.invoke(main, [
            "analyze", csv_path,
            "--algorithm", "fges",
            "--output", str(tmp_path / "output"),
        ])
        assert result.exit_code == 0
        assert "Edges found" in result.output
