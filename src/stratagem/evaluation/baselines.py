"""Baseline defender strategies for comparison against the Stackelberg solver.

This module provides three non-game-theoretic strategies that a defender
might use to allocate deception assets.  All three share the same interface
as the Stackelberg solver — they accept a topology, budget, and utility
parameters, and return a StackelbergSolution — so benchmarking is
apples-to-apples.

─── Baselines ────────────────────────────────────────────────────────────

1. **Uniform Random** — Spreads budget evenly across all nodes using the
   cheapest asset type (honeytokens, cost=1.0).  Maximizes coverage breadth
   at the expense of detection quality.

2. **Static (Value-Based)** — Greedily covers the highest-value nodes
   first using the most effective asset (honeypots, det=0.85).  Falls back
   to cheaper assets as budget runs low.  This is the "common sense"
   strategy: protect what matters most.

3. **Heuristic (Centrality-Based)** — Greedily covers the nodes with
   highest degree centrality using honeypots.  The intuition is that
   highly connected nodes sit on more potential attack paths, so covering
   them intercepts the attacker at chokepoints.

─── Why These Three? ─────────────────────────────────────────────────────

These baselines represent the three most natural strategies a defender
might use without game-theoretic reasoning:

- Uniform is the maximum-entropy strategy (no information used).
- Static uses node values (the defender's own loss function).
- Heuristic uses network structure (topological information).

The Stackelberg solver combines both value and structure *and* accounts
for the attacker's strategic response, so it should weakly dominate all
three.  Demonstrating this dominance is the purpose of benchmarking.

─── Attacker Best Response ───────────────────────────────────────────────

Given any fixed defender coverage, the attacker's best response is to
target the node t that maximizes their expected utility:

    t* = argmax_t  EU_a(c, t)
       = argmax_t  p(t) · U_a^c(t) + (1 − p(t)) · U_a^u(t)

where p(t) = Σ_a c_{t,a} · det_prob(a) is the effective detection
probability.  Ties are broken in the defender's favor, consistent with
the Strong Stackelberg Equilibrium convention.
"""

from __future__ import annotations

import networkx as nx
import numpy as np

from stratagem.environment.deception import (
    ASSET_COSTS,
    ASSET_DETECTION_PROBS,
    DeceptionType,
)
from stratagem.environment.network import NetworkTopology
from stratagem.game.solver import StackelbergSolution, UtilityParams


# ───────────────────────────────────────────────────────────────────────
# Attacker best response (shared across all baselines)
# ───────────────────────────────────────────────────────────────────────


def _attacker_best_response(
    topology: NetworkTopology,
    detection_probs: dict[str, float],
    params: UtilityParams,
) -> tuple[str, float, float]:
    """Find the attacker's optimal target given a fixed coverage.

    Computes EU_a(t) for each node and returns the target that maximizes
    attacker utility.  Ties are broken in the defender's favor (the
    standard SSE convention).

    Args:
        topology: Network topology with node values.
        detection_probs: Effective detection probability per node.
        params: Utility scaling parameters.

    Returns:
        (target_node_id, attacker_eu, defender_eu) at the best response.
    """
    best_target = ""
    best_attacker_eu = -np.inf
    best_defender_eu = -np.inf

    for nid in topology.nodes:
        v = topology.get_attrs(nid).value
        p = detection_probs.get(nid, 0.0)
        a_eu = p * (-params.beta * v) + (1 - p) * v
        d_eu = p * (params.alpha * v) + (1 - p) * (-v)

        if a_eu > best_attacker_eu + 1e-8:
            # Strict improvement: take this target.
            best_target = nid
            best_attacker_eu = a_eu
            best_defender_eu = d_eu
        elif abs(a_eu - best_attacker_eu) < 1e-8 and d_eu > best_defender_eu:
            # Tie in attacker EU: break in defender's favor.
            best_target = nid
            best_defender_eu = d_eu

    return best_target, float(best_attacker_eu), float(best_defender_eu)


def _build_solution(
    topology: NetworkTopology,
    coverage: dict[str, dict[DeceptionType, float]],
    params: UtilityParams,
) -> StackelbergSolution:
    """Build a StackelbergSolution from a coverage vector.

    Computes detection probabilities, the attacker's best response, and
    expected utilities — everything needed for the solution struct.
    """
    # Compute effective detection probabilities: p(t) = Σ_a c_{t,a} · det_prob(a).
    detection_probs: dict[str, float] = {}
    for nid in topology.nodes:
        p = 0.0
        for atype, prob in coverage.get(nid, {}).items():
            p += prob * ASSET_DETECTION_PROBS[atype]
        detection_probs[nid] = p

    target, attacker_eu, defender_eu = _attacker_best_response(
        topology, detection_probs, params
    )

    return StackelbergSolution(
        coverage=coverage,
        attacker_target=target,
        defender_expected_utility=defender_eu,
        attacker_expected_utility=attacker_eu,
        detection_probabilities=detection_probs,
    )


# ───────────────────────────────────────────────────────────────────────
# Baseline 1: Uniform Random
# ───────────────────────────────────────────────────────────────────────


def uniform_baseline(
    topology: NetworkTopology,
    budget: float,
    params: UtilityParams | None = None,
) -> StackelbergSolution:
    """Spread budget evenly across all nodes using honeytokens.

    Strategy: allocate budget / n to each node, then place a honeytoken
    with probability min(per_node_budget / cost_honeytoken, 1.0).

    This is the maximum-entropy baseline — it uses no information about
    node values or network structure.  It maximizes coverage *breadth*
    by using the cheapest asset type (honeytoken, cost=1.0, det=0.50).

    Args:
        topology: Network topology.
        budget: Total deception budget.
        params: Utility parameters (defaults to α=β=1).

    Returns:
        StackelbergSolution with uniform coverage.
    """
    if params is None:
        params = UtilityParams()

    nodes = topology.nodes
    n = len(nodes)
    ht_cost = ASSET_COSTS[DeceptionType.HONEYTOKEN]

    # Per-node budget share.
    per_node = budget / n if n > 0 else 0.0
    # Coverage probability: fraction of a honeytoken we can afford per node.
    # Capped at 1.0 (can't place more than one asset).
    coverage_prob = min(per_node / ht_cost, 1.0) if ht_cost > 0 else 0.0

    coverage: dict[str, dict[DeceptionType, float]] = {}
    for nid in nodes:
        if coverage_prob > 1e-8:
            coverage[nid] = {DeceptionType.HONEYTOKEN: coverage_prob}
        else:
            coverage[nid] = {}

    return _build_solution(topology, coverage, params)


# ───────────────────────────────────────────────────────────────────────
# Baseline 2: Static (Value-Based)
# ───────────────────────────────────────────────────────────────────────


def static_baseline(
    topology: NetworkTopology,
    budget: float,
    params: UtilityParams | None = None,
) -> StackelbergSolution:
    """Greedily cover the highest-value nodes with the best assets.

    Strategy: sort nodes by value (descending), then for each node in
    order, place the most effective affordable asset.  Preference order:
    honeypot (det=0.85, cost=3.0) > decoy credential (det=0.70, cost=1.5)
    > honeytoken (det=0.50, cost=1.0).

    This is the "protect the crown jewels" strategy — it focuses all
    budget on the nodes the defender values most.  It ignores network
    structure and the attacker's strategic response.

    Args:
        topology: Network topology.
        budget: Total deception budget.
        params: Utility parameters (defaults to α=β=1).

    Returns:
        StackelbergSolution with value-greedy coverage.
    """
    if params is None:
        params = UtilityParams()

    coverage = _greedy_allocate(
        topology,
        budget,
        ranking=sorted(
            topology.nodes,
            key=lambda nid: topology.get_attrs(nid).value,
            reverse=True,
        ),
    )

    return _build_solution(topology, coverage, params)


# ───────────────────────────────────────────────────────────────────────
# Baseline 3: Heuristic (Centrality-Based)
# ───────────────────────────────────────────────────────────────────────


def heuristic_baseline(
    topology: NetworkTopology,
    budget: float,
    params: UtilityParams | None = None,
) -> StackelbergSolution:
    """Greedily cover the most-connected nodes with the best assets.

    Strategy: sort nodes by degree centrality (descending), then for each
    node in order, place the most effective affordable asset.  Degree
    centrality = (number of neighbors) / (n − 1).

    The intuition: highly connected nodes are network chokepoints.  An
    attacker must traverse them to reach deeper targets, so placing
    deception assets there maximizes the chance of interception.

    This uses topological information but ignores node values and the
    attacker's strategic reasoning.

    Args:
        topology: Network topology.
        budget: Total deception budget.
        params: Utility parameters (defaults to α=β=1).

    Returns:
        StackelbergSolution with centrality-greedy coverage.
    """
    if params is None:
        params = UtilityParams()

    # Degree centrality: fraction of possible edges each node has.
    centrality = nx.degree_centrality(topology.graph)

    coverage = _greedy_allocate(
        topology,
        budget,
        ranking=sorted(
            topology.nodes,
            key=lambda nid: centrality[nid],
            reverse=True,
        ),
    )

    return _build_solution(topology, coverage, params)


# ───────────────────────────────────────────────────────────────────────
# Shared greedy allocation
# ───────────────────────────────────────────────────────────────────────

# Asset types ordered by detection effectiveness (best first).
_ASSET_PREFERENCE = [
    DeceptionType.HONEYPOT,
    DeceptionType.DECOY_CREDENTIAL,
    DeceptionType.HONEYTOKEN,
]


def _greedy_allocate(
    topology: NetworkTopology,
    budget: float,
    ranking: list[str],
) -> dict[str, dict[DeceptionType, float]]:
    """Greedily assign assets to nodes in the given priority order.

    For each node (in `ranking` order), attempt to place the most
    effective asset type that fits the remaining budget.  If the best
    asset is too expensive, try cheaper ones.  Assets are placed
    deterministically (probability = 1.0).

    Args:
        topology: Network topology.
        budget: Remaining budget.
        ranking: Node IDs in priority order (highest priority first).

    Returns:
        Coverage dict mapping node_id → {asset_type → probability}.
    """
    remaining = budget
    coverage: dict[str, dict[DeceptionType, float]] = {nid: {} for nid in topology.nodes}

    for nid in ranking:
        if remaining < ASSET_COSTS[DeceptionType.HONEYTOKEN]:
            break  # Can't afford even the cheapest asset.
        for atype in _ASSET_PREFERENCE:
            cost = ASSET_COSTS[atype]
            if cost <= remaining + 1e-8:
                coverage[nid] = {atype: 1.0}
                remaining -= cost
                break

    return coverage
