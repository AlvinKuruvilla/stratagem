"""Tests for the Stackelberg equilibrium solver.

These tests verify the mathematical properties that any valid SSE must
satisfy, rather than hardcoding specific numeric solutions.  This makes
them robust to changes in topology or utility parameters.
"""

import numpy as np
import pytest

from stratagem.environment.deception import ASSET_COSTS, ASSET_DETECTION_PROBS, DeceptionType
from stratagem.environment.network import (
    NetworkTopology,
    NodeAttributes,
    NodeType,
    OS,
    Service,
)
from stratagem.game.solver import (
    StackelbergSolution,
    UtilityParams,
    solve_stackelberg,
)


# ── Helpers ───────────────────────────────────────────────────────────


def _attacker_eu(node_value: float, p_detect: float, params: UtilityParams) -> float:
    """Compute the attacker's expected utility at a node.

    EU_a(t) = p(t) · U_a^c(t)  +  (1 − p(t)) · U_a^u(t)
            = p(t) · (−β·v(t))  +  (1 − p(t)) · v(t)
    """
    return p_detect * (-params.beta * node_value) + (1 - p_detect) * node_value


def _total_cost(solution: StackelbergSolution) -> float:
    """Sum of expected deployment costs across all nodes."""
    total = 0.0
    for assets in solution.coverage.values():
        for atype, prob in assets.items():
            total += prob * ASSET_COSTS[atype]
    return total


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def small_topo() -> NetworkTopology:
    return NetworkTopology.small_enterprise()


@pytest.fixture
def params() -> UtilityParams:
    return UtilityParams(alpha=1.0, beta=1.0)


@pytest.fixture
def two_node_topo() -> NetworkTopology:
    """Minimal 2-node topology for hand-verifiable tests."""
    topo = NetworkTopology(name="two_node")
    topo.add_node("low", NodeAttributes(NodeType.WORKSTATION, OS.LINUX, [Service.SSH], 2.0))
    topo.add_node("high", NodeAttributes(NodeType.DATABASE, OS.LINUX, [Service.SSH], 10.0))
    topo.add_edge("low", "high")
    return topo


# ── Equilibrium property tests ────────────────────────────────────────


class TestEquilibriumProperties:
    """Verify that the solver output satisfies SSE properties."""

    def test_attacker_best_response(self, small_topo, params):
        """The attacker's target must yield the highest attacker EU.

        At equilibrium, EU_a(c, t*) ≥ EU_a(c, t) for all t ≠ t*.
        """
        sol = solve_stackelberg(small_topo, budget=10.0, params=params)
        target_eu = sol.attacker_expected_utility

        for nid in small_topo.nodes:
            if nid == sol.attacker_target:
                continue
            node_value = small_topo.get_attrs(nid).value
            p_det = sol.detection_probabilities[nid]
            other_eu = _attacker_eu(node_value, p_det, params)
            assert target_eu >= other_eu - 1e-6, (
                f"Attacker prefers {nid} (EU={other_eu:.4f}) over "
                f"{sol.attacker_target} (EU={target_eu:.4f})"
            )

    def test_coverage_probabilities_valid(self, small_topo):
        """All c_{t,a} must be in [0, 1] and Σ_a c_{t,a} ≤ 1."""
        sol = solve_stackelberg(small_topo, budget=10.0)

        for nid, assets in sol.coverage.items():
            total = 0.0
            for atype, prob in assets.items():
                assert prob >= -1e-8, f"Negative probability at {nid}/{atype}: {prob}"
                assert prob <= 1.0 + 1e-8, f"Probability > 1 at {nid}/{atype}: {prob}"
                total += prob
            assert total <= 1.0 + 1e-8, (
                f"Total coverage at {nid} exceeds 1: {total}"
            )

    def test_budget_constraint_satisfied(self, small_topo):
        """Total expected deployment cost must not exceed the budget."""
        budget = 10.0
        sol = solve_stackelberg(small_topo, budget=budget)
        total_cost = _total_cost(sol)
        assert total_cost <= budget + 1e-6, (
            f"Budget exceeded: {total_cost:.4f} > {budget}"
        )

    def test_detection_probabilities_consistent(self, small_topo):
        """p(t) must equal Σ_a c_{t,a} · det_prob(a)."""
        sol = solve_stackelberg(small_topo, budget=10.0)
        asset_types = list(DeceptionType)
        det_probs = [ASSET_DETECTION_PROBS[a] for a in asset_types]

        for nid in small_topo.nodes:
            expected_p = 0.0
            for a_idx, atype in enumerate(asset_types):
                prob = sol.coverage[nid].get(atype, 0.0)
                expected_p += prob * det_probs[a_idx]
            assert abs(sol.detection_probabilities[nid] - expected_p) < 1e-6, (
                f"Inconsistent detection prob at {nid}: "
                f"stored={sol.detection_probabilities[nid]:.6f}, "
                f"computed={expected_p:.6f}"
            )


class TestDefenderUtility:
    """Verify that the defender benefits from the Stackelberg strategy."""

    def test_defender_eu_matches_formula(self, small_topo, params):
        """Defender EU must match the formula at the attacker's target.

        EU_d = p(t*) · U_d^c(t*) + (1 − p(t*)) · U_d^u(t*)
        """
        sol = solve_stackelberg(small_topo, budget=10.0, params=params)
        t_star = sol.attacker_target
        v = small_topo.get_attrs(t_star).value
        p = sol.detection_probabilities[t_star]
        expected_eu = p * (params.alpha * v) + (1 - p) * (-v)
        assert abs(sol.defender_expected_utility - expected_eu) < 1e-6

    def test_dominates_zero_coverage(self, small_topo, params):
        """SSE defender EU must be ≥ the zero-coverage baseline.

        With zero coverage, the attacker targets the highest-value node
        and always succeeds: EU_d = −max(v(t)).
        """
        sol = solve_stackelberg(small_topo, budget=10.0, params=params)
        max_value = max(small_topo.get_attrs(n).value for n in small_topo.nodes)
        zero_coverage_eu = -max_value
        assert sol.defender_expected_utility >= zero_coverage_eu - 1e-6


class TestBudgetEdgeCases:
    """Test behavior at budget extremes."""

    def test_zero_budget(self, small_topo, params):
        """With zero budget, no assets are deployed.

        The attacker targets the highest-value node and always succeeds.
        """
        sol = solve_stackelberg(small_topo, budget=0.0, params=params)

        # No coverage anywhere.
        for nid in small_topo.nodes:
            assert sol.detection_probabilities[nid] < 1e-8

        # Attacker targets highest-value node.
        max_value = max(small_topo.get_attrs(n).value for n in small_topo.nodes)
        target_value = small_topo.get_attrs(sol.attacker_target).value
        assert target_value == max_value

        # Defender EU = −v(target).
        assert abs(sol.defender_expected_utility - (-max_value)) < 1e-6

    def test_large_budget_improves_defender_eu(self, small_topo, params):
        """More budget should weakly improve the defender's utility."""
        sol_low = solve_stackelberg(small_topo, budget=5.0, params=params)
        sol_high = solve_stackelberg(small_topo, budget=20.0, params=params)
        assert sol_high.defender_expected_utility >= sol_low.defender_expected_utility - 1e-6


class TestTwoNodeTopology:
    """Tests on a minimal topology for easier reasoning."""

    def test_targets_high_value_with_no_budget(self, two_node_topo, params):
        """Attacker should target the high-value node when no defense."""
        sol = solve_stackelberg(two_node_topo, budget=0.0, params=params)
        assert sol.attacker_target == "high"
        assert abs(sol.defender_expected_utility - (-10.0)) < 1e-6

    def test_equilibrium_valid(self, two_node_topo, params):
        """Verify all SSE properties on the 2-node topology."""
        sol = solve_stackelberg(two_node_topo, budget=5.0, params=params)

        # Best response.
        target_eu = sol.attacker_expected_utility
        for nid in two_node_topo.nodes:
            if nid == sol.attacker_target:
                continue
            v = two_node_topo.get_attrs(nid).value
            p = sol.detection_probabilities[nid]
            other_eu = _attacker_eu(v, p, params)
            assert target_eu >= other_eu - 1e-6

        # Budget.
        assert _total_cost(sol) <= 5.0 + 1e-6


class TestUtilityParams:
    """Test that varying α and β changes the equilibrium."""

    def test_higher_alpha_helps_defender(self, small_topo):
        """Increasing α (detection reward) should weakly improve defender EU."""
        sol_default = solve_stackelberg(small_topo, budget=10.0, params=UtilityParams(1.0, 1.0))
        sol_high_alpha = solve_stackelberg(small_topo, budget=10.0, params=UtilityParams(2.0, 1.0))
        assert sol_high_alpha.defender_expected_utility >= sol_default.defender_expected_utility - 1e-6

    def test_higher_beta_helps_defender(self, small_topo):
        """Increasing β (attacker penalty) should weakly improve defender EU.

        A higher β makes the attacker more averse to covered nodes, giving
        the defender more leverage with the same coverage.
        """
        sol_default = solve_stackelberg(small_topo, budget=10.0, params=UtilityParams(1.0, 1.0))
        sol_high_beta = solve_stackelberg(small_topo, budget=10.0, params=UtilityParams(1.0, 2.0))
        assert sol_high_beta.defender_expected_utility >= sol_default.defender_expected_utility - 1e-6


class TestSolverOutput:
    """Test output structure and summary formatting."""

    def test_solution_has_all_nodes(self, small_topo):
        """Coverage dict should include an entry for every node."""
        sol = solve_stackelberg(small_topo, budget=10.0)
        for nid in small_topo.nodes:
            assert nid in sol.coverage
            assert nid in sol.detection_probabilities

    def test_attacker_target_is_valid_node(self, small_topo):
        sol = solve_stackelberg(small_topo, budget=10.0)
        assert sol.attacker_target in small_topo.nodes

    def test_summary_is_nonempty(self, small_topo):
        sol = solve_stackelberg(small_topo, budget=10.0)
        summary = sol.summary()
        assert len(summary) > 0
        assert sol.attacker_target in summary


class TestMediumTopology:
    """Sanity checks on the medium topology to catch scaling issues."""

    def test_medium_solves_successfully(self):
        topo = NetworkTopology.medium_enterprise()
        sol = solve_stackelberg(topo, budget=15.0)
        assert sol.attacker_target in topo.nodes
        assert _total_cost(sol) <= 15.0 + 1e-6

    def test_medium_best_response_valid(self):
        topo = NetworkTopology.medium_enterprise()
        params = UtilityParams()
        sol = solve_stackelberg(topo, budget=15.0, params=params)
        target_eu = sol.attacker_expected_utility
        for nid in topo.nodes:
            if nid == sol.attacker_target:
                continue
            v = topo.get_attrs(nid).value
            p = sol.detection_probabilities[nid]
            other_eu = _attacker_eu(v, p, params)
            assert target_eu >= other_eu - 1e-6
