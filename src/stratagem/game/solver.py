"""Stackelberg equilibrium solver for deception-based network security games.

This module computes the Strong Stackelberg Equilibrium (SSE) for an
attacker-defender game played over a simulated enterprise network. The
defender (leader) commits to a randomized deception deployment strategy;
the attacker (follower) observes this commitment and selects an optimal
target node.

─── Background ───────────────────────────────────────────────────────────

A *Stackelberg security game* (SSG) models security resource allocation as
a leader-follower game. The defender moves first, publicly committing to a
(possibly randomized) protection plan.  The attacker observes this plan and
chooses a best-response target.  The solution concept is the *Strong
Stackelberg Equilibrium* (SSE), which is guaranteed to exist and is unique
in expected utility [1].

The key insight from the SSG literature is that the defender benefits from
*commitment power*: by committing to a mixed strategy, the defender can
shape the attacker's incentives.  In general-sum games, SSE gives the
defender strictly higher utility than any Nash equilibrium [3].

─── Our Model ────────────────────────────────────────────────────────────

    Players:
        Defender (leader)  — allocates deception assets to network nodes.
        Attacker (follower) — observes the allocation, picks one node to attack.

    Defender strategy space (ERASER heterogeneous-resource formulation [2]):
        The defender has three deception asset types, each with a different
        cost and detection probability:

            Asset Type          Detection Prob    Cost
            ─────────────────   ──────────────    ────
            Honeypot            0.85              3.0
            Decoy Credential    0.70              1.5
            Honeytoken          0.50              1.0

        A *pure strategy* is a budget-feasible assignment of assets to nodes.
        A *mixed strategy* is a probability distribution over pure strategies.
        Rather than enumerate the (exponentially many) pure strategies, we
        work with *marginal coverage probabilities*:

            c_{t,a} ∈ [0, 1]  =  probability that asset type a is placed on node t

        This compact representation is justified by the Birkhoff-von Neumann
        decomposition theorem: any feasible coverage vector can be realized
        as a mixture of pure strategies [2].

    Attacker strategy space:
        The attacker selects a single target node t ∈ T.  This is the
        standard formulation used in ARMOR [4], IRIS [5], and ERASER [2].
        (Path-based attacker strategies are deferred to future work.)

    Utility model (general-sum):
        Each node t has a value v(t) representing the defender's loss if it
        is compromised.  Payoffs depend on whether the attacker is detected:

            U_d^c(t) = +α · v(t)    defender payoff when attacker is caught at t
            U_d^u(t) = −v(t)         defender payoff when attacker succeeds at t
            U_a^c(t) = −β · v(t)    attacker payoff when caught at t
            U_a^u(t) = +v(t)         attacker payoff when succeeding at t

        Here α ≥ 0 scales the defender's detection reward and β ≥ 0 scales
        the attacker's detection penalty.  With α = β = 1 the game is close
        to zero-sum but not exactly; general-sum is standard in the SSG
        literature because commitment power only helps in general-sum [3].

    Effective detection probability:
        Given coverage vector c, the probability of detecting an attacker
        who targets node t is:

            p(t) = Σ_a  c_{t,a} · det_prob(a)

        This is the expected detection probability across all realizations
        of the defender's mixed strategy (in any single realization, at most
        one asset is placed on a node, with the constraint Σ_a c_{t,a} ≤ 1).

    Expected utilities:
        When the attacker targets node t under coverage vector c:

            EU_d(c, t) = p(t) · U_d^c(t)  +  (1 − p(t)) · U_d^u(t)
            EU_a(c, t) = p(t) · U_a^c(t)  +  (1 − p(t)) · U_a^u(t)

─── Solver Algorithm ─────────────────────────────────────────────────────

We use the *Multiple LPs* approach [1], specialized to security games with
heterogeneous resources [2].

For each candidate attacker target t*, we solve a linear program that
finds the defender's optimal coverage vector under the constraint that t*
is the attacker's best response.  The LP yielding the highest defender
utility gives the SSE.

    LP(t*):

        maximize    EU_d(c, t*)

        subject to:
            (i)    Σ_a c_{t,a} ≤ 1                  ∀ t        (at most one asset per node)
            (ii)   Σ_{t,a} c_{t,a} · cost(a) ≤ B               (budget)
            (iii)  EU_a(c, t*) ≥ EU_a(c, t)          ∀ t ≠ t*  (t* is best response)
            (iv)   0 ≤ c_{t,a} ≤ 1                   ∀ t, a    (probability bounds)

    Derivation of the linear forms:

        Let Δ_d(t) = U_d^c(t) − U_d^u(t) = (α + 1) · v(t)  > 0
        Let Δ_a(t) = U_a^c(t) − U_a^u(t) = −(β + 1) · v(t) < 0

        The objective becomes:
            EU_d(c, t*) = p(t*) · Δ_d(t*) + U_d^u(t*)
                        = [Σ_a c_{t*,a} · det_a] · Δ_d(t*)  +  U_d^u(t*)

        Since U_d^u(t*) is constant, we maximize  Σ_a c_{t*,a} · det_a · Δ_d(t*).
        (scipy.optimize.linprog minimizes, so we negate the objective.)

        The best-response constraint (iii) expands to:
            p(t) · Δ_a(t)  −  p(t*) · Δ_a(t*)  ≤  U_a^u(t*) − U_a^u(t)

        which is:
            Σ_a c_{t,a} · det_a · Δ_a(t)  −  Σ_a c_{t*,a} · det_a · Δ_a(t*)
                ≤  v(t*) − v(t)

        All constraints are linear in the c_{t,a} variables.

    Procedure:
        1. Solve LP(t*) for each node t* in the topology.
        2. Skip infeasible LPs (no coverage can make t* the best response).
        3. Return the solution with the highest defender expected utility.

    Complexity:
        n LPs, each with O(n · A) variables and O(n) constraints, where
        n = number of nodes and A = number of asset types (3).  Solved in
        polynomial time via the HiGHS simplex/interior-point solver.

─── References ───────────────────────────────────────────────────────────

[1] V. Conitzer and T. Sandholm, "Computing the optimal strategy to commit
    to," in Proc. ACM EC, 2006.
[2] C. Kiekintveld, M. Jain, J. Tsai, J. Pita, F. Ordóñez, and M. Tambe,
    "Computing optimal randomized resource allocations for massive security
    games," in Proc. AAMAS, 2009.
[3] V. Conitzer and T. Sandholm, "Stackelberg vs. Nash in security games:
    An extended investigation of interchangeability, equivalence, and
    uniqueness," JAIR, vol. 41, 2011.
[4] J. Pita et al., "Deployed ARMOR protection: The application of a game
    theoretic model for security at the Los Angeles International Airport,"
    in Proc. AAMAS, 2008.
[5] J. Tsai et al., "IRIS — A tool for strategic security allocation in
    transportation networks," in Proc. AAMAS, 2009.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import linprog

from stratagem.environment.deception import ASSET_COSTS, ASSET_DETECTION_PROBS, DeceptionType
from stratagem.environment.network import NetworkTopology


# ───────────────────────────────────────────────────────────────────────
# Utility model
# ───────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class UtilityParams:
    """Scaling parameters for the general-sum utility model.

    Attributes:
        alpha: Defender detection reward scale.  U_d^c(t) = α · v(t).
        beta:  Attacker detection penalty scale.  U_a^c(t) = −β · v(t).

    With α = β = 1, payoffs are nearly zero-sum.  Varying α and β lets us
    model asymmetric stakes — e.g. a defender who values early detection
    more than the node's intrinsic worth (α > 1).
    """

    alpha: float = 1.0
    beta: float = 1.0


def defender_covered_utility(node_value: float, params: UtilityParams) -> float:
    """U_d^c(t) = +α · v(t).  Defender's payoff when the attacker is detected."""
    return params.alpha * node_value


def defender_uncovered_utility(node_value: float) -> float:
    """U_d^u(t) = −v(t).  Defender's payoff when the attacker succeeds."""
    return -node_value


def attacker_covered_utility(node_value: float, params: UtilityParams) -> float:
    """U_a^c(t) = −β · v(t).  Attacker's payoff when caught."""
    return -params.beta * node_value


def attacker_uncovered_utility(node_value: float) -> float:
    """U_a^u(t) = +v(t).  Attacker's payoff when succeeding."""
    return node_value


# ───────────────────────────────────────────────────────────────────────
# Solver output
# ───────────────────────────────────────────────────────────────────────


@dataclass
class StackelbergSolution:
    """Result of computing the Strong Stackelberg Equilibrium.

    Attributes:
        coverage: node_id → {asset_type → probability}.  The defender's
            optimal mixed strategy as marginal coverage probabilities.
            Only entries with probability > 0 are included.
        attacker_target: The attacker's best-response target node.
        defender_expected_utility: EU_d at equilibrium.
        attacker_expected_utility: EU_a at equilibrium.
        detection_probabilities: node_id → p(t), the effective detection
            probability at each node (Σ_a c_{t,a} · det_prob(a)).
    """

    coverage: dict[str, dict[DeceptionType, float]]
    attacker_target: str
    defender_expected_utility: float
    attacker_expected_utility: float
    detection_probabilities: dict[str, float]

    def summary(self) -> str:
        """Human-readable summary of the equilibrium."""
        lines = [
            f"Attacker target: {self.attacker_target}",
            f"Defender EU: {self.defender_expected_utility:+.4f}",
            f"Attacker EU: {self.attacker_expected_utility:+.4f}",
            "",
            "Coverage (non-zero):",
        ]
        for nid, assets in sorted(self.coverage.items()):
            if not assets:
                continue
            parts = [f"{atype.value}={prob:.3f}" for atype, prob in assets.items()]
            p_det = self.detection_probabilities[nid]
            lines.append(f"  {nid}: {', '.join(parts)}  (p_detect={p_det:.3f})")
        return "\n".join(lines)


# ───────────────────────────────────────────────────────────────────────
# Solver
# ───────────────────────────────────────────────────────────────────────

# Numerical tolerance for filtering near-zero coverage probabilities.
_EPS = 1e-8


def solve_stackelberg(
    topology: NetworkTopology,
    budget: float,
    params: UtilityParams | None = None,
) -> StackelbergSolution:
    """Compute the Strong Stackelberg Equilibrium for a deception game.

    Args:
        topology: The network topology (nodes with values, edges).
        budget: Total budget available for deception asset deployment.
        params: Utility scaling parameters (defaults to α=β=1).

    Returns:
        A StackelbergSolution containing the defender's optimal mixed
        strategy, the attacker's best-response target, and the expected
        utilities for both players.

    Raises:
        RuntimeError: If all LPs are infeasible (should never happen since
            zero coverage is always a feasible solution).
    """
    if params is None:
        params = UtilityParams()

    nodes = topology.nodes
    n = len(nodes)
    asset_types = list(DeceptionType)
    num_asset_types = len(asset_types)  # A = 3 (honeypot, decoy, honeytoken)
    num_vars = n * num_asset_types      # One c_{t,a} per (node, asset type) pair.

    # ── Pre-compute asset parameters ──────────────────────────────────
    # costs[a]     = deployment cost of asset type a
    # det_probs[a] = detection probability of asset type a
    costs = np.array([ASSET_COSTS[a] for a in asset_types])
    det_probs = np.array([ASSET_DETECTION_PROBS[a] for a in asset_types])

    # ── Pre-compute per-node utility terms ────────────────────────────
    # v[t]      = value of node t
    # Ud_c[t]   = U_d^c(t) = +α · v(t)
    # Ud_u[t]   = U_d^u(t) = −v(t)
    # Ua_c[t]   = U_a^c(t) = −β · v(t)
    # Ua_u[t]   = U_a^u(t) = +v(t)
    # delta_d[t] = Δ_d(t) = U_d^c(t) − U_d^u(t) = (α+1) · v(t) > 0
    # delta_a[t] = Δ_a(t) = U_a^c(t) − U_a^u(t) = −(β+1) · v(t) < 0
    values = np.array([topology.get_attrs(nid).value for nid in nodes])
    Ud_c = params.alpha * values
    Ud_u = -values
    Ua_c = -params.beta * values
    Ua_u = values.copy()
    delta_d = Ud_c - Ud_u  # (α+1) · v(t), always positive for v(t) > 0
    delta_a = Ua_c - Ua_u  # −(β+1) · v(t), always negative for v(t) > 0

    # ── Variable indexing ─────────────────────────────────────────────
    # Variable j = t * A + a  corresponds to  c_{t,a}.
    def var_idx(t: int, a: int) -> int:
        return t * num_asset_types + a

    # ── Variable bounds: 0 ≤ c_{t,a} ≤ 1 ─────────────────────────────
    bounds = [(0.0, 1.0)] * num_vars

    # ── Shared inequality constraints (A_ub @ x ≤ b_ub) ──────────────
    # These constraints are identical across all LPs; only the objective
    # and best-response constraints change per candidate target.

    # Constraint (i):  Σ_a c_{t,a} ≤ 1  for each node t.
    # Interpretation: at most one asset is deployed per node in any
    # single realization of the mixed strategy.
    A_one_per_node = np.zeros((n, num_vars))
    for t in range(n):
        for a in range(num_asset_types):
            A_one_per_node[t, var_idx(t, a)] = 1.0
    b_one_per_node = np.ones(n)

    # Constraint (ii):  Σ_{t,a} c_{t,a} · cost(a) ≤ B.
    # Interpretation: expected total deployment cost stays within budget.
    A_budget = np.zeros((1, num_vars))
    for t in range(n):
        for a in range(num_asset_types):
            A_budget[0, var_idx(t, a)] = costs[a]
    b_budget = np.array([budget])

    # ── Solve one LP per candidate attacker target ────────────────────
    best_solution: StackelbergSolution | None = None
    best_defender_eu = -np.inf

    for t_star in range(n):
        # ── Objective (minimize for linprog, so negate) ───────────────
        #
        # maximize  EU_d(c, t*)
        #   = p(t*) · Δ_d(t*) + U_d^u(t*)
        #   = [Σ_a c_{t*,a} · det_prob(a)] · Δ_d(t*)  +  constant
        #
        # Only variables c_{t*,a} appear in the objective.
        c_obj = np.zeros(num_vars)
        for a in range(num_asset_types):
            c_obj[var_idx(t_star, a)] = -det_probs[a] * delta_d[t_star]

        # ── Best-response constraints (iii) ───────────────────────────
        #
        # For each t ≠ t*, require EU_a(c, t*) ≥ EU_a(c, t):
        #
        #   Σ_a c_{t,a} · det_a · Δ_a(t)
        #     − Σ_a c_{t*,a} · det_a · Δ_a(t*)
        #       ≤  v(t*) − v(t)
        #
        # This is n−1 linear constraints.
        n_br = n - 1
        A_br = np.zeros((n_br, num_vars))
        b_br = np.zeros(n_br)

        row = 0
        for t in range(n):
            if t == t_star:
                continue
            # Coefficients for c_{t,a}: det_prob(a) · Δ_a(t)
            for a in range(num_asset_types):
                A_br[row, var_idx(t, a)] = det_probs[a] * delta_a[t]
            # Coefficients for c_{t*,a}: −det_prob(a) · Δ_a(t*)
            for a in range(num_asset_types):
                A_br[row, var_idx(t_star, a)] -= det_probs[a] * delta_a[t_star]
            # RHS: U_a^u(t*) − U_a^u(t) = v(t*) − v(t)
            b_br[row] = Ua_u[t_star] - Ua_u[t]
            row += 1

        # ── Assemble and solve ────────────────────────────────────────
        A_ub = np.vstack([A_one_per_node, A_budget, A_br])
        b_ub = np.concatenate([b_one_per_node, b_budget, b_br])

        result = linprog(c_obj, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")

        if not result.success:
            # LP infeasible: no coverage vector can make t* the attacker's
            # best response.  Skip to the next candidate.
            continue

        # Recover the true objective (add back the constant U_d^u(t*)).
        defender_eu = -result.fun + Ud_u[t_star]

        if defender_eu > best_defender_eu:
            best_defender_eu = defender_eu

            # ── Parse solution into structured output ─────────────────
            x = result.x
            coverage: dict[str, dict[DeceptionType, float]] = {}
            det_probs_out: dict[str, float] = {}

            for t in range(n):
                nid = nodes[t]
                asset_coverage: dict[DeceptionType, float] = {}
                p_detect = 0.0
                for a_idx, atype in enumerate(asset_types):
                    prob = float(x[var_idx(t, a_idx)])
                    # Filter out numerically negligible values.
                    if prob > _EPS:
                        asset_coverage[atype] = prob
                    p_detect += prob * det_probs[a_idx]
                coverage[nid] = asset_coverage
                det_probs_out[nid] = max(p_detect, 0.0)

            # Attacker's expected utility at the target node.
            p_star = det_probs_out[nodes[t_star]]
            attacker_eu = float(p_star * Ua_c[t_star] + (1 - p_star) * Ua_u[t_star])

            best_solution = StackelbergSolution(
                coverage=coverage,
                attacker_target=nodes[t_star],
                defender_expected_utility=float(defender_eu),
                attacker_expected_utility=attacker_eu,
                detection_probabilities=det_probs_out,
            )

    if best_solution is None:
        # This should never happen: with c = 0 (zero coverage), the
        # attacker's best response is the highest-value node, and that LP
        # is feasible with objective = U_d^u(highest-value node).
        raise RuntimeError(
            "All LPs infeasible. This indicates a bug in the constraint "
            "formulation — zero coverage should always be feasible."
        )

    return best_solution
