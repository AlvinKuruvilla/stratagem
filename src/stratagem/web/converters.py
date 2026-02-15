"""Convert solver data structures to API response models."""

from __future__ import annotations

from stratagem.environment.network import NetworkTopology
from stratagem.game.solver import StackelbergSolution, UtilityParams
from stratagem.web.schemas import NodeUtilityBreakdown, SolutionResponse


def solution_to_response(
    solution: StackelbergSolution,
    topology: NetworkTopology,
    budget: float,
    params: UtilityParams,
) -> SolutionResponse:
    """Convert a StackelbergSolution into a SolutionResponse with per-node breakdowns."""
    breakdowns: list[NodeUtilityBreakdown] = []

    for nid in topology.nodes:
        attrs = topology.get_attrs(nid)
        v = attrs.value
        p = solution.detection_probabilities.get(nid, 0.0)

        # Coverage dict for this node (asset_type string → probability)
        node_coverage = {
            atype.value: prob
            for atype, prob in solution.coverage.get(nid, {}).items()
        }

        # Utility terms
        ud_c = params.alpha * v
        ud_u = -v
        ua_c = -params.beta * v
        ua_u = v

        # Expected utilities at this node
        eu_d = p * ud_c + (1 - p) * ud_u
        eu_a = p * ua_c + (1 - p) * ua_u

        breakdowns.append(
            NodeUtilityBreakdown(
                node_id=nid,
                value=v,
                detection_probability=p,
                coverage=node_coverage,
                is_entry_point=attrs.is_entry_point,
                defender_covered_utility=ud_c,
                defender_uncovered_utility=ud_u,
                attacker_covered_utility=ua_c,
                attacker_uncovered_utility=ua_u,
                defender_expected_utility=eu_d,
                attacker_expected_utility=eu_a,
            )
        )

    return SolutionResponse(
        topology_name=topology.name,
        budget=budget,
        alpha=params.alpha,
        beta=params.beta,
        attacker_target=solution.attacker_target,
        defender_expected_utility=solution.defender_expected_utility,
        attacker_expected_utility=solution.attacker_expected_utility,
        node_breakdowns=breakdowns,
    )
