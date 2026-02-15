"""Tests for the benchmark runner."""

import json
import tempfile
from pathlib import Path

import pytest

from stratagem.environment.network import NetworkTopology
from stratagem.evaluation.benchmark import (
    BenchmarkConfig,
    BenchmarkResult,
    export_results_csv,
    export_results_json,
    run_benchmark,
    run_game_sync,
)
from stratagem.evaluation.metrics import TrialResult, extract_trial_result
from stratagem.web.game_runner import compute_attacker_path, strategy_to_defender_actions

# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def small_topo() -> NetworkTopology:
    return NetworkTopology.small_enterprise()


@pytest.fixture
def defender_actions(small_topo) -> list[tuple[str, str]]:
    return strategy_to_defender_actions(small_topo, budget=10.0, strategy="sse_optimal")


@pytest.fixture
def attacker_path(small_topo) -> list[str]:
    entry = small_topo.entry_points()[0]
    return compute_attacker_path(small_topo, entry)


# ── TestSyncGameRunner ───────────────────────────────────────────────


class TestSyncGameRunner:
    def test_returns_final_state(self, small_topo, defender_actions, attacker_path):
        state = run_game_sync(
            topology=small_topo,
            budget=10.0,
            max_rounds=10,
            seed=42,
            defender_actions=defender_actions,
            attacker_path=attacker_path,
        )
        assert isinstance(state, dict)
        assert "winner" in state
        assert state["winner"] in ("defender", "attacker")
        assert state["game_over"] is True

    def test_deterministic_with_same_seed(self, small_topo, defender_actions, attacker_path):
        state1 = run_game_sync(
            topology=small_topo,
            budget=10.0,
            max_rounds=10,
            seed=42,
            defender_actions=defender_actions,
            attacker_path=attacker_path,
        )
        state2 = run_game_sync(
            topology=small_topo,
            budget=10.0,
            max_rounds=10,
            seed=42,
            defender_actions=defender_actions,
            attacker_path=attacker_path,
        )
        assert state1["winner"] == state2["winner"]
        assert state1["current_round"] == state2["current_round"]
        assert state1["attacker"]["exfiltrated_value"] == state2["attacker"]["exfiltrated_value"]

    def test_game_terminates(self, small_topo, defender_actions, attacker_path):
        state = run_game_sync(
            topology=small_topo,
            budget=10.0,
            max_rounds=5,
            seed=42,
            defender_actions=defender_actions,
            attacker_path=attacker_path,
        )
        assert state["game_over"] is True
        rounds_played = state["current_round"] - 1
        assert 0 <= rounds_played <= 5

    def test_extract_trial_from_sync(self, small_topo, defender_actions, attacker_path):
        state = run_game_sync(
            topology=small_topo,
            budget=10.0,
            max_rounds=10,
            seed=42,
            defender_actions=defender_actions,
            attacker_path=attacker_path,
        )
        trial = extract_trial_result(state, "sse_optimal", "small", 42)
        assert isinstance(trial, TrialResult)
        assert trial.strategy == "sse_optimal"
        assert trial.topology == "small"


# ── TestBenchmarkRunner ──────────────────────────────────────────────


class TestBenchmarkRunner:
    def test_all_combos_present(self):
        config = BenchmarkConfig(
            topologies=["small"],
            strategies=["sse_optimal", "uniform"],
            num_trials=5,
            max_rounds=5,
        )
        result = run_benchmark(config)

        strategies_seen = {m.strategy for m in result.strategy_metrics}
        assert "sse_optimal" in strategies_seen
        assert "uniform" in strategies_seen

    def test_correct_trial_count(self):
        config = BenchmarkConfig(
            topologies=["small"],
            strategies=["sse_optimal"],
            num_trials=10,
            max_rounds=5,
        )
        result = run_benchmark(config)
        assert len(result.trial_results) == 10

    def test_small_benchmark_completes(self):
        config = BenchmarkConfig(
            topologies=["small"],
            strategies=["sse_optimal", "uniform", "static", "heuristic"],
            num_trials=3,
            max_rounds=5,
        )
        result = run_benchmark(config)
        assert isinstance(result, BenchmarkResult)
        assert len(result.strategy_metrics) == 4  # 4 strategies x 1 topology
        assert len(result.trial_results) == 12  # 4 strategies x 3 trials

    def test_progress_callback(self):
        calls = []

        def callback(desc, current, total):
            calls.append((desc, current, total))

        config = BenchmarkConfig(
            topologies=["small"],
            strategies=["sse_optimal"],
            num_trials=3,
            max_rounds=3,
        )
        run_benchmark(config, progress_callback=callback)
        assert len(calls) == 3
        assert calls[-1][1] == calls[-1][2]  # last call: current == total

    def test_multiple_topologies(self):
        config = BenchmarkConfig(
            topologies=["small", "medium"],
            strategies=["sse_optimal"],
            num_trials=3,
            max_rounds=5,
        )
        result = run_benchmark(config)
        topologies_seen = {m.topology for m in result.strategy_metrics}
        assert "small" in topologies_seen
        assert "medium" in topologies_seen
        assert len(result.trial_results) == 6  # 1 strategy x 2 topos x 3 trials


# ── TestExport ───────────────────────────────────────────────────────


class TestExport:
    @pytest.fixture
    def small_result(self) -> BenchmarkResult:
        config = BenchmarkConfig(
            topologies=["small"],
            strategies=["sse_optimal", "uniform"],
            num_trials=3,
            max_rounds=5,
        )
        return run_benchmark(config)

    def test_json_creates_valid_file(self, small_result):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = Path(f.name)

        export_results_json(small_result, path)
        assert path.exists()
        assert path.stat().st_size > 0

        data = json.loads(path.read_text())
        assert "strategy_metrics" in data
        assert "trial_results" in data
        assert "comparisons" in data

        path.unlink()

    def test_csv_has_correct_headers(self, small_result):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = Path(f.name)

        export_results_csv(small_result.trial_results, path)
        assert path.exists()

        lines = path.read_text().strip().split("\n")
        headers = lines[0].split(",")
        assert "strategy" in headers
        assert "topology" in headers
        assert "detected" in headers
        assert "exfiltrated_value" in headers

        # Rows = header + trials.
        assert len(lines) == 1 + len(small_result.trial_results)

        path.unlink()

    def test_csv_empty_trials(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = Path(f.name)

        export_results_csv([], path)
        # Should not write anything for empty trials.
        # File may or may not exist depending on implementation.
        path.unlink(missing_ok=True)
