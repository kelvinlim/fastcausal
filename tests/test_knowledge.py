"""Tests for fastcausal.knowledge — knowledge dict creation and prior file parsing."""

import os
import tempfile

import pytest

from fastcausal.knowledge import create_lag_knowledge, read_prior_file, dict_to_knowledge


class TestCreateLagKnowledge:
    def test_basic(self):
        cols = ["X", "Y", "Z"]
        k = create_lag_knowledge(cols)
        assert "addtemporal" in k
        assert k["addtemporal"][0] == ["X_lag", "Y_lag", "Z_lag"]
        assert k["addtemporal"][1] == ["X", "Y", "Z"]

    def test_custom_stub(self):
        k = create_lag_knowledge(["A", "B"], lag_stub="_prev")
        assert k["addtemporal"][0] == ["A_prev", "B_prev"]
        assert k["addtemporal"][1] == ["A", "B"]

    def test_empty_columns(self):
        k = create_lag_knowledge([])
        assert k["addtemporal"][0] == []
        assert k["addtemporal"][1] == []


class TestReadPriorFile:
    def test_temporal_tiers(self, tmp_path):
        prior = tmp_path / "prior.txt"
        prior.write_text(
            "/knowledge\n"
            "addtemporal\n"
            "0 X_lag Y_lag\n"
            "1 X Y\n"
        )
        k = read_prior_file(str(prior))
        assert k["addtemporal"][0] == ["X_lag", "Y_lag"]
        assert k["addtemporal"][1] == ["X", "Y"]

    def test_forbidden_edges(self, tmp_path):
        prior = tmp_path / "prior.txt"
        prior.write_text(
            "/knowledge\n"
            "forbiddirect\n"
            "X Y\n"
            "A B\n"
        )
        k = read_prior_file(str(prior))
        assert ("X", "Y") in k["forbiddirect"]
        assert ("A", "B") in k["forbiddirect"]

    def test_required_edges(self, tmp_path):
        prior = tmp_path / "prior.txt"
        prior.write_text(
            "/knowledge\n"
            "requiredirect\n"
            "X Y\n"
        )
        k = read_prior_file(str(prior))
        assert ("X", "Y") in k["requiredirect"]

    def test_mixed_sections(self, tmp_path):
        prior = tmp_path / "prior.txt"
        prior.write_text(
            "/knowledge\n"
            "addtemporal\n"
            "0 A_lag\n"
            "1 A\n"
            "forbiddirect\n"
            "A A_lag\n"
            "requiredirect\n"
            "A_lag A\n"
        )
        k = read_prior_file(str(prior))
        assert k["addtemporal"][0] == ["A_lag"]
        assert ("A", "A_lag") in k["forbiddirect"]
        assert ("A_lag", "A") in k["requiredirect"]

    def test_comments_and_blanks(self, tmp_path):
        prior = tmp_path / "prior.txt"
        prior.write_text(
            "/knowledge\n"
            "# this is a comment\n"
            "\n"
            "addtemporal\n"
            "0 X_lag\n"
            "1 X\n"
        )
        k = read_prior_file(str(prior))
        assert k["addtemporal"][0] == ["X_lag"]

    def test_boston_prior_file(self):
        """Test reading the bundled boston prior file."""
        prior_path = os.path.join(
            os.path.dirname(__file__), "..", "fastcausal", "data", "boston_prior.txt"
        )
        if not os.path.exists(prior_path):
            pytest.skip("Boston prior file not found")
        k = read_prior_file(prior_path)
        assert "addtemporal" in k
        assert 1 in k["addtemporal"]
        assert 2 in k["addtemporal"]


class TestDictToKnowledge:
    def test_none_returns_none(self):
        assert dict_to_knowledge(None) is None

    def test_temporal_tiers(self):
        kd = {"addtemporal": {0: ["X_lag"], 1: ["X"]}}
        k = dict_to_knowledge(kd)
        assert k is not None

    def test_forbidden(self):
        kd = {"forbiddirect": [("X", "Y")]}
        k = dict_to_knowledge(kd)
        assert k is not None

    def test_required(self):
        kd = {"requiredirect": [("X", "Y")]}
        k = dict_to_knowledge(kd)
        assert k is not None

    def test_full_knowledge(self):
        kd = {
            "addtemporal": {0: ["X_lag", "Y_lag"], 1: ["X", "Y"]},
            "forbiddirect": [("X", "X_lag")],
            "requiredirect": [("X_lag", "X")],
        }
        k = dict_to_knowledge(kd)
        assert k is not None
