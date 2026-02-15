"""Tests for the baseline defender strategies.

Tests verify:
  - Coverage validity (probabilities in range, at most one asset per node, budget)
  - Attacker best response correctness
  - Characteristic behavior of each baseline
  - SSE dominance: the Stackelberg solver should weakly dominate all baselines
"""

import networkx as nx
import pytest

from stratagem.environment.deception import ASSET_COSTS, ASSET_DETECTION_PROBS, DeceptionType
from stratagem.environment.network import (
    NetworkTopology,
    NodeAttributes,
    NodeType,
    OS,
    Service,
)
from stratagem.evaluation.baselines import (
    heuristic_baseline,
    static_baseline,
    uniform_baseline,
)
from stratagem.game.solver import (
    StackelbergSolution,
    UtilityParams,
    solve_stackelberg,
)


# ── Helpers ───────────────────────────────────────────────────────────


def _total_cost(solution: StackelbergSolution) -> float:
    total = 0.0
    for assets in solution.coverage.values():
        for atype, prob in assets.items():
            total += prob * ASSET_COSTS[atype]
    return total


def _attacker_eu_at(nid: str, topo: NetworkTopology, sol: StackelbergSolution, params: UtilityParams) -> float:
    v = topo.get_attrs(nid).value
    p = sol.detection_probabilities[nid]
    return p * (-params.beta * v) + (1 - p) * v


def _assert_valid_solution(sol: StackelbergSolution, topo: NetworkTopology, budget: float, params: UtilityParams):
    """Assert that a solution satisfies all validity properties."""
    # Coverage probabilities in [0, 1].
    for nid, assets in sol.coverage.items():
        total = 0.0
        for atype, prob in assets.items():
            assert prob >= -1e-8, f"Negative prob at {nid}"
            assert prob <= 1.0 + 1e-8, f"Prob > 1 at {nid}"
            total += prob
        assert total <= 1.0 + 1e-8, f"Total coverage > 1 at {nid}"

    # Budget constraint.
    assert _total_cost(sol) <= budget + 1e-6

    # Attacker target is a valid node.
    assert sol.attacker_target in topo.nodes

    # Attacker best response: target EU ≥ all others.
    target_eu = sol.attacker_expected_utility
    for nid in topo.nodes:
        if nid == sol.attacker_target:
            continue
        other_eu = _attacker_eu_at(nid, topo, sol, params)
        assert target_eu >= other_eu - 1e-6, (
            f"Attacker prefers {nid} (EU={other_eu:.4f}) over "
            f"{sol.attacker_target} (EU={target_eu:.4f})"
        )


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def small_topo() -> NetworkTopology:
    return NetworkTopology.small_enterprise()


@pytest.fixture
def params() -> UtilityParams:
    return UtilityParams(alpha=1.0, beta=1.0)


# ── Uniform Baseline Tests ────────────────────────────────────────────


class TestUniformBaseline:
    def test_valid_solution(self, small_topo, params):
        sol = uniform_baseline(small_topo, budget=10.0, params=params)
        _assert_valid_solution(sol, small_topo, 10.0, params)

    def test_even_coverage(self, small_topo):
        """All nodes should have the same coverage probability."""
        sol = uniform_baseline(small_topo, budget=10.0)
        probs = list(sol.detection_probabilities.values())
        # All detection probs should be equal (uniform).
        assert max(probs) - min(probs) < 1e-8

    def test_uses_honeytokens(self, small_topo):
        """Uniform baseline should use honeytokens (cheapest asset)."""
        sol = uniform_baseline(small_topo, budget=10.0)
        for nid, assets in sol.coverage.items():
            for atype in assets:
                assert atype == DeceptionType.HONEYTOKEN

    def test_zero_budget(self, small_topo, params):
        """Zero budget should produce zero coverage."""
        sol = uniform_baseline(small_topo, budget=0.0, params=params)
        for nid in small_topo.nodes:
            assert sol.detection_probabilities[nid] < 1e-8

    def test_large_budget_caps_at_one(self, small_topo):
        """Coverage probability should cap at 1.0 even with excess budget."""
        sol = uniform_baseline(small_topo, budget=1000.0)
        for nid in small_topo.nodes:
            assets = sol.coverage[nid]
            for prob in assets.values():
                assert prob <= 1.0 + 1e-8


# ── Static Baseline Tests ─────────────────────────────────────────────


class TestStaticBaseline:
    def test_valid_solution(self, small_topo, params):
        sol = static_baseline(small_topo, budget=10.0, params=params)
        _assert_valid_solution(sol, small_topo, 10.0, params)

    def test_covers_highest_value_nodes(self, small_topo):
        """The covered nodes should be the highest-value ones."""
        sol = static_baseline(small_topo, budget=10.0)

        # Find which nodes were covered.
        covered = [nid for nid, assets in sol.coverage.items() if assets]
        uncovered = [nid for nid, assets in sol.coverage.items() if not assets]

        if covered and uncovered:
            # The minimum value among covered nodes should be ≥ the
            # maximum value among uncovered nodes.
            min_covered_value = min(small_topo.get_attrs(n).value for n in covered)
            max_uncovered_value = max(small_topo.get_attrs(n).value for n in uncovered)
            assert min_covered_value >= max_uncovered_value

    def test_prefers_honeypots(self, small_topo):
        """Should place honeypots (most effective) when affordable."""
        sol = static_baseline(small_topo, budget=10.0)
        # At least one honeypot should be deployed with budget=10.
        has_honeypot = any(
            DeceptionType.HONEYPOT in assets
            for assets in sol.coverage.values()
        )
        assert has_honeypot

    def test_deterministic_placement(self, small_topo):
        """Coverage probabilities should be 0 or 1 (pure strategy)."""
        sol = static_baseline(small_topo, budget=10.0)
        for nid, assets in sol.coverage.items():
            for prob in assets.values():
                assert abs(prob - 1.0) < 1e-8 or abs(prob) < 1e-8

    def test_zero_budget(self, small_topo, params):
        sol = static_baseline(small_topo, budget=0.0, params=params)
        for nid in small_topo.nodes:
            assert sol.detection_probabilities[nid] < 1e-8


# ── Heuristic Baseline Tests ──────────────────────────────────────────


class TestHeuristicBaseline:
    def test_valid_solution(self, small_topo, params):
        sol = heuristic_baseline(small_topo, budget=10.0, params=params)
        _assert_valid_solution(sol, small_topo, 10.0, params)

    def test_covers_high_centrality_nodes(self, small_topo):
        """Covered nodes should have higher centrality than uncovered ones."""
        sol = heuristic_baseline(small_topo, budget=10.0)
        centrality = nx.degree_centrality(small_topo.graph)

        covered = [nid for nid, assets in sol.coverage.items() if assets]
        uncovered = [nid for nid, assets in sol.coverage.items() if not assets]

        if covered and uncovered:
            min_covered_cent = min(centrality[n] for n in covered)
            max_uncovered_cent = max(centrality[n] for n in uncovered)
            assert min_covered_cent >= max_uncovered_cent - 1e-8

    def test_deterministic_placement(self, small_topo):
        """Coverage probabilities should be 0 or 1 (pure strategy)."""
        sol = heuristic_baseline(small_topo, budget=10.0)
        for nid, assets in sol.coverage.items():
            for prob in assets.values():
                assert abs(prob - 1.0) < 1e-8 or abs(prob) < 1e-8

    def test_zero_budget(self, small_topo, params):
        sol = heuristic_baseline(small_topo, budget=0.0, params=params)
        for nid in small_topo.nodes:
            assert sol.detection_probabilities[nid] < 1e-8


# ── SSE Dominance Tests ───────────────────────────────────────────────


class TestStackelbergDominance:
    """The SSE should weakly dominate all baselines.

    By construction, the Stackelberg solver finds the defender strategy
    that maximizes defender EU subject to the attacker best-responding.
    Any other strategy (including these baselines) must give the defender
    weakly lower EU when facing a rational attacker.
    """

    @pytest.fixture
    def sse(self, small_topo, params) -> StackelbergSolution:
        return solve_stackelberg(small_topo, budget=10.0, params=params)

    def test_dominates_uniform(self, small_topo, params, sse):
        baseline = uniform_baseline(small_topo, budget=10.0, params=params)
        assert sse.defender_expected_utility >= baseline.defender_expected_utility - 1e-6

    def test_dominates_static(self, small_topo, params, sse):
        baseline = static_baseline(small_topo, budget=10.0, params=params)
        assert sse.defender_expected_utility >= baseline.defender_expected_utility - 1e-6

    def test_dominates_heuristic(self, small_topo, params, sse):
        baseline = heuristic_baseline(small_topo, budget=10.0, params=params)
        assert sse.defender_expected_utility >= baseline.defender_expected_utility - 1e-6

    def test_dominance_on_medium_topology(self):
        """SSE dominance should hold across topology sizes."""
        topo = NetworkTopology.medium_enterprise()
        params = UtilityParams()
        budget = 15.0

        sse = solve_stackelberg(topo, budget=budget, params=params)
        for baseline_fn in [uniform_baseline, static_baseline, heuristic_baseline]:
            baseline = baseline_fn(topo, budget=budget, params=params)
            assert sse.defender_expected_utility >= baseline.defender_expected_utility - 1e-6, (
                f"SSE (EU={sse.defender_expected_utility:.4f}) does not dominate "
                f"{baseline_fn.__name__} (EU={baseline.defender_expected_utility:.4f})"
            )


# ── Cross-Baseline Comparison ─────────────────────────────────────────


class TestBaselineComparison:
    """Sanity checks on relative baseline behavior."""

    def test_all_baselines_return_solutions(self, small_topo, params):
        """All baselines should return valid StackelbergSolution objects."""
        for fn in [uniform_baseline, static_baseline, heuristic_baseline]:
            sol = fn(small_topo, budget=10.0, params=params)
            assert isinstance(sol, StackelbergSolution)
            assert sol.attacker_target in small_topo.nodes

    def test_summary_nonempty(self, small_topo):
        """All baselines should produce non-empty summaries."""
        for fn in [uniform_baseline, static_baseline, heuristic_baseline]:
            sol = fn(small_topo, budget=10.0)
            assert len(sol.summary()) > 0
