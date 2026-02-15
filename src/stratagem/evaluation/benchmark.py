"""Benchmark runner: synchronous game execution and orchestration.

The Play mode in ``web/game_runner.py`` streams games over SSE with pacing
delays.  The benchmark needs the same game logic but running at full speed
without any async or network formatting.  ``run_game_sync`` provides that:
same create/evaluate flow, synchronous, no sleeps, returns the final state.

The orchestrator (``run_benchmark``) sweeps over strategies and topologies,
collects ``TrialResult`` objects, then aggregates them with the metrics
engine.

Export helpers dump the full ``BenchmarkResult`` to JSON or per-trial rows
to CSV for downstream analysis.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path

from stratagem.agents.stubs import create_stub_attacker, create_stub_defender
from stratagem.environment.network import NetworkTopology
from stratagem.evaluation.metrics import (
    PairwiseComparison,
    StrategyMetrics,
    TrialResult,
    compare_all_pairs,
    compute_metrics,
    extract_trial_result,
)
from stratagem.game.graph import create_initial_state, evaluate_round
from stratagem.web.game_runner import compute_attacker_path, strategy_to_defender_actions

# ── Synchronous game runner ───────────────────────────────────────────


def run_game_sync(
    topology: NetworkTopology,
    budget: float,
    max_rounds: int,
    seed: int,
    defender_actions: list[tuple[str, str]],
    attacker_path: list[str],
) -> dict:
    """Run a complete game synchronously and return the final state.

    Same logic as ``run_game_stream`` in ``web/game_runner.py`` but without
    async, SSE formatting, or sleep delays.  This is the inner loop of the
    benchmark and must be fast.
    """
    entry_point = attacker_path[0] if attacker_path else topology.entry_points()[0]

    defender_node = create_stub_defender(defender_actions)
    attacker_node = create_stub_attacker(attacker_path, seed=seed)

    state = create_initial_state(
        topology, budget, max_rounds, entry_point=entry_point, seed=seed,
    )

    # Defender setup (one-time).
    update = defender_node(state)
    state = {**state, **update}

    # Round loop.
    for _round_num in range(1, max_rounds + 1):
        # Attacker acts.
        update = attacker_node(state)
        state = {**state, **update}

        # Evaluate round (detection, win conditions).
        update = evaluate_round(state)
        state = {**state, **update}

        if state.get("game_over", False):
            break

    return state


# ── Configuration ─────────────────────────────────────────────────────

TOPOLOGIES = {
    "small": NetworkTopology.small_enterprise,
    "medium": NetworkTopology.medium_enterprise,
    "large": NetworkTopology.large_enterprise,
}


@dataclass
class BenchmarkConfig:
    topologies: list[str] = field(
        default_factory=lambda: ["small", "medium", "large"],
    )
    strategies: list[str] = field(
        default_factory=lambda: ["sse_optimal", "uniform", "static", "heuristic"],
    )
    num_trials: int = 100
    max_rounds: int = 10
    budget: float = 10.0
    base_seed: int = 42


@dataclass
class BenchmarkResult:
    config: BenchmarkConfig
    strategy_metrics: list[StrategyMetrics]
    comparisons: list[PairwiseComparison]
    trial_results: list[TrialResult]


# ── Orchestrator ──────────────────────────────────────────────────────


def run_benchmark(
    config: BenchmarkConfig,
    progress_callback: Callable[[str, int, int], None] | None = None,
) -> BenchmarkResult:
    """Run the full benchmark sweep and return aggregated results.

    For each (topology, strategy) pair, runs ``config.num_trials`` games
    with deterministic seeds.  All strategies share the same attacker path
    per topology for fair comparison.

    Args:
        config: Benchmark parameters.
        progress_callback: Optional ``(description, current, total)`` hook
            for progress bars.

    Returns:
        ``BenchmarkResult`` with per-strategy metrics and pairwise tests.
    """
    total_runs = (
        len(config.topologies) * len(config.strategies) * config.num_trials
    )
    current = 0
    all_trials: list[TrialResult] = []

    for topo_name in config.topologies:
        factory = TOPOLOGIES.get(topo_name)
        if factory is None:
            continue
        topology = factory()

        # Shared attacker path for this topology.
        entry_point = topology.entry_points()[0]
        attacker_path = compute_attacker_path(topology, entry_point)

        # Pre-compute defender actions per strategy (deterministic).
        defender_actions_map: dict[str, list[tuple[str, str]]] = {}
        for strategy in config.strategies:
            defender_actions_map[strategy] = strategy_to_defender_actions(
                topology, config.budget, strategy,
            )

        for strategy in config.strategies:
            defender_actions = defender_actions_map[strategy]

            for i in range(config.num_trials):
                seed = config.base_seed + i

                final_state = run_game_sync(
                    topology=topology,
                    budget=config.budget,
                    max_rounds=config.max_rounds,
                    seed=seed,
                    defender_actions=defender_actions,
                    attacker_path=attacker_path,
                )

                trial = extract_trial_result(
                    final_state, strategy, topo_name, seed,
                )
                all_trials.append(trial)

                current += 1
                if progress_callback:
                    progress_callback(
                        f"{topo_name}/{strategy}", current, total_runs,
                    )

    # Aggregate metrics per (strategy, topology).
    strategy_metrics: list[StrategyMetrics] = []
    for topo_name in config.topologies:
        # Group trials by strategy for pairwise comparison.
        by_strategy: dict[str, list[TrialResult]] = {}
        for strategy in config.strategies:
            matching = [
                t for t in all_trials
                if t.strategy == strategy and t.topology == topo_name
            ]
            by_strategy[strategy] = matching
            if matching:
                strategy_metrics.append(
                    compute_metrics(matching, strategy, topo_name),
                )

    # Pairwise statistical comparisons (across all topologies combined).
    by_strategy_all: dict[str, list[TrialResult]] = {}
    for strategy in config.strategies:
        by_strategy_all[strategy] = [
            t for t in all_trials if t.strategy == strategy
        ]
    comparisons = compare_all_pairs(by_strategy_all)

    return BenchmarkResult(
        config=config,
        strategy_metrics=strategy_metrics,
        comparisons=comparisons,
        trial_results=all_trials,
    )


# ── Export helpers ────────────────────────────────────────────────────


class _DataclassEncoder(json.JSONEncoder):
    """JSON encoder that handles dataclasses and special float values."""

    def default(self, o):
        if hasattr(o, "__dataclass_fields__"):
            return asdict(o)
        return super().default(o)


def export_results_json(result: BenchmarkResult, path: str | Path) -> None:
    """Write the full BenchmarkResult to a JSON file."""
    path = Path(path)
    with path.open("w") as f:
        json.dump(asdict(result), f, cls=_DataclassEncoder, indent=2, default=str)


def export_results_csv(trial_results: list[TrialResult], path: str | Path) -> None:
    """Write one row per TrialResult to a CSV file."""
    path = Path(path)
    if not trial_results:
        return

    fieldnames = list(trial_results[0].__dataclass_fields__.keys())

    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for trial in trial_results:
            writer.writerow(asdict(trial))
