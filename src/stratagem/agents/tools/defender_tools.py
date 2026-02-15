"""Defender agent tools — closures over a GameContext."""

from __future__ import annotations

from langchain_core.tools import tool

from stratagem.agents.context import GameContext
from stratagem.environment.deception import (
    decoy_credential,
    honeypot,
    honeytoken,
)
from stratagem.environment.network import Service
from stratagem.game.solver import StackelbergSolution, solve_stackelberg


def create_defender_tools(ctx: GameContext) -> list:
    """Build the 7 defender tools, each closed over the shared GameContext."""

    @tool
    def inspect_topology() -> str:
        """View the network topology: nodes, edges, and their attributes."""
        topo = ctx.topology
        lines = [f"Topology: {topo.name} ({topo.node_count} nodes)"]
        lines.append("")
        lines.append("Nodes:")
        for nid in sorted(topo.nodes):
            attrs = topo.get_attrs(nid)
            services = ", ".join(s.value for s in attrs.services)
            entry = " [ENTRY]" if attrs.is_entry_point else ""
            lines.append(
                f"  {nid}: type={attrs.node_type.value} os={attrs.os.value} "
                f"services=[{services}] value={attrs.value:.1f}{entry}"
            )
        lines.append("")
        lines.append("Edges:")
        for src, dst, data in topo.graph.edges(data=True):
            lines.append(f"  {src} <-> {dst} (segment={data.get('segment', 'default')})")
        return "\n".join(lines)

    @tool
    def get_node_value(node_id: str) -> str:
        """Check the value and attributes of a specific node."""
        if node_id not in ctx.topology.nodes:
            return f"Error: node '{node_id}' does not exist."
        attrs = ctx.topology.get_attrs(node_id)
        neighbors = ctx.topology.neighbors(node_id)
        return (
            f"Node {node_id}: type={attrs.node_type.value} os={attrs.os.value} "
            f"value={attrs.value:.1f} entry={attrs.is_entry_point} "
            f"services=[{', '.join(s.value for s in attrs.services)}] "
            f"neighbors=[{', '.join(neighbors)}]"
        )

    @tool
    def get_budget() -> str:
        """Check remaining defender budget and what has been spent."""
        d = ctx.defender
        deployed = len(d.deployed_assets)
        return (
            f"Budget: {d.remaining_budget:.1f} remaining "
            f"(total={d.budget:.1f}, spent={d.total_spent:.1f}, "
            f"deployed_assets={deployed})"
        )

    @tool
    def deploy_honeypot(node_id: str) -> str:
        """Deploy a honeypot on a node (cost 3.0, detection_prob 0.85).

        Honeypots are the most expensive but most reliable deception asset.
        Any attacker interaction with the fake service is suspicious.
        """
        if node_id not in ctx.topology.nodes:
            return f"Error: node '{node_id}' does not exist."
        asset = honeypot(node_id, Service.HTTP)
        if not ctx.defender.deploy(asset):
            return (
                f"Failed: insufficient budget. Need 3.0, "
                f"have {ctx.defender.remaining_budget:.1f}."
            )
        return (
            f"Honeypot deployed on {node_id}. "
            f"Remaining budget: {ctx.defender.remaining_budget:.1f}"
        )

    @tool
    def deploy_decoy_credential(node_id: str) -> str:
        """Deploy a decoy credential on a node (cost 1.5, detection_prob 0.70).

        Medium cost and detection probability. The attacker may use the fake
        credential, revealing their presence.
        """
        if node_id not in ctx.topology.nodes:
            return f"Error: node '{node_id}' does not exist."
        asset = decoy_credential(node_id)
        if not ctx.defender.deploy(asset):
            return (
                f"Failed: insufficient budget. Need 1.5, "
                f"have {ctx.defender.remaining_budget:.1f}."
            )
        return (
            f"Decoy credential deployed on {node_id}. "
            f"Remaining budget: {ctx.defender.remaining_budget:.1f}"
        )

    @tool
    def deploy_honeytoken(node_id: str) -> str:
        """Deploy a honeytoken on a node (cost 1.0, detection_prob 0.50).

        Cheapest option but lower detection probability. A fake data artifact
        that may alert when accessed.
        """
        if node_id not in ctx.topology.nodes:
            return f"Error: node '{node_id}' does not exist."
        asset = honeytoken(node_id)
        if not ctx.defender.deploy(asset):
            return (
                f"Failed: insufficient budget. Need 1.0, "
                f"have {ctx.defender.remaining_budget:.1f}."
            )
        return (
            f"Honeytoken deployed on {node_id}. "
            f"Remaining budget: {ctx.defender.remaining_budget:.1f}"
        )

    @tool
    def get_solver_recommendation() -> str:
        """Query the Stackelberg equilibrium solver for an optimal deployment strategy.

        Returns the SSE-optimal coverage probabilities and attacker target prediction.
        Use this to inform your deployment decisions.
        """
        solution: StackelbergSolution = solve_stackelberg(
            ctx.topology, ctx.defender.remaining_budget
        )
        lines = [solution.summary()]
        lines.append("")
        lines.append("Suggested deployments (highest coverage nodes):")
        ranked = sorted(
            solution.detection_probabilities.items(), key=lambda x: x[1], reverse=True
        )
        for nid, p_det in ranked[:5]:
            if p_det < 0.01:
                break
            assets = solution.coverage.get(nid, {})
            parts = []
            for atype, prob in assets.items():
                if prob > 0.01:
                    parts.append(f"{atype.value}={prob:.2f}")
            if parts:
                lines.append(f"  {nid}: {', '.join(parts)} (p_detect={p_det:.2f})")
        return "\n".join(lines)

    return [
        inspect_topology,
        get_node_value,
        get_budget,
        deploy_honeypot,
        deploy_decoy_credential,
        deploy_honeytoken,
        get_solver_recommendation,
    ]
