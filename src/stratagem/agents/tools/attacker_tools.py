"""Attacker agent tools — closures over a GameContext."""

from __future__ import annotations

from langchain_core.tools import tool

from stratagem.agents.context import GameContext
from stratagem.environment.attack_surface import (
    TECHNIQUE_BY_ID,
    AccessLevel,
    get_applicable_techniques,
)

# Probability that a deception asset is visible during a scan (partial observability).
_DEFAULT_DECEPTION_VISIBILITY = 0.3


def create_attacker_tools(
    ctx: GameContext,
    deception_visibility: float = _DEFAULT_DECEPTION_VISIBILITY,
) -> list:
    """Build the 5 attacker tools, each closed over the shared GameContext."""

    @tool
    def scan_network() -> str:
        """Discover neighbors from the current position (partial observability).

        Returns visible adjacent nodes with their basic attributes. Deception
        assets may or may not be revealed depending on detection probability.
        """
        position = ctx.attacker.position
        neighbors = ctx.topology.neighbors(position)
        if not neighbors:
            return f"No neighbors visible from {position}."

        lines = [f"Scan from {position} — {len(neighbors)} neighbor(s):"]
        for nid in neighbors:
            attrs = ctx.topology.get_attrs(nid)
            services = ", ".join(s.value for s in attrs.services)
            access = ctx.attacker.access_levels.get(nid, AccessLevel.NONE)
            line = (
                f"  {nid}: type={attrs.node_type.value} os={attrs.os.value}"
                f" services=[{services}]"
            )
            if access != AccessLevel.NONE:
                line += f" access={access.value}"
            # Partial observability: deception assets revealed probabilistically.
            assets_here = ctx.defender.assets_on_node(nid)
            for asset in assets_here:
                if ctx.rng.random() < deception_visibility:
                    line += f" [SUSPICIOUS: possible {asset.asset_type.value}]"
            lines.append(line)

        # Record the scan action.
        ctx.actions_this_round.append({
            "action": "scan",
            "node_id": position,
            "technique_id": "T1046",
        })
        return "\n".join(lines)

    @tool
    def probe_node(node_id: str) -> str:
        """Probe a node to check its services and OS in detail.

        This action is recorded and may trigger detection if the node has
        deception assets deployed.
        """
        if node_id not in ctx.topology.nodes:
            return f"Error: node '{node_id}' does not exist."

        attrs = ctx.topology.get_attrs(node_id)
        access = ctx.attacker.access_levels.get(node_id, AccessLevel.NONE)
        applicable = get_applicable_techniques(attrs, access)

        lines = [
            f"Probe result for {node_id}:",
            f"  Type: {attrs.node_type.value}",
            f"  OS: {attrs.os.value}",
            f"  Services: {', '.join(s.value for s in attrs.services)}",
            f"  Current access: {access.value}",
            f"  Applicable techniques ({len(applicable)}):",
        ]
        for tech in applicable:
            lines.append(
                f"    {tech.id} ({tech.name}): success={tech.base_success_rate:.0%} "
                f"noise={tech.noise:.2f} grants={tech.grants_access.value}"
            )

        ctx.actions_this_round.append({
            "action": "probe",
            "node_id": node_id,
            "technique_id": "T1046",
        })
        return "\n".join(lines)

    @tool
    def execute_technique(technique_id: str, target_node: str) -> str:
        """Execute an ATT&CK technique against a target node.

        Validates that the technique is applicable, then rolls for success.
        On success, updates access level on the target node.
        """
        if target_node not in ctx.topology.nodes:
            return f"Error: node '{target_node}' does not exist."

        tech = TECHNIQUE_BY_ID.get(technique_id)
        if tech is None:
            return f"Error: unknown technique '{technique_id}'."

        attrs = ctx.topology.get_attrs(target_node)
        access = ctx.attacker.access_levels.get(target_node, AccessLevel.NONE)

        # Validate access requirement.
        access_order = [AccessLevel.NONE, AccessLevel.USER, AccessLevel.ROOT]
        if access_order.index(access) < access_order.index(tech.required_access):
            return (
                f"Failed: {tech.id} requires {tech.required_access.value} access on "
                f"{target_node}, but you have {access.value}."
            )

        # Validate applicability (OS, services).
        if not tech.applicable_to(attrs):
            return (
                f"Failed: {tech.id} ({tech.name}) is not applicable to {target_node} "
                f"(os={attrs.os.value}, services={[s.value for s in attrs.services]})."
            )

        # Record the action before rolling.
        ctx.actions_this_round.append({
            "action": "execute",
            "node_id": target_node,
            "technique_id": technique_id,
            "noise": tech.noise,
        })

        # Roll for success.
        roll = ctx.rng.random()
        if roll > tech.base_success_rate:
            return (
                f"{tech.id} ({tech.name}) failed against {target_node}. "
                f"(roll={roll:.2f} > success_rate={tech.base_success_rate:.2f})"
            )

        # Success — upgrade access level.
        current_rank = access_order.index(
            ctx.attacker.access_levels.get(target_node, AccessLevel.NONE)
        )
        granted_rank = access_order.index(tech.grants_access)
        if granted_rank > current_rank:
            ctx.attacker.access_levels[target_node] = tech.grants_access

        if target_node not in ctx.attacker.compromised_nodes:
            ctx.attacker.compromised_nodes.append(target_node)
            ctx.topology.set_compromised(target_node)

        return (
            f"{tech.id} ({tech.name}) succeeded on {target_node}! "
            f"Access: {tech.grants_access.value}."
        )

    @tool
    def move_lateral(target_node: str) -> str:
        """Move to an adjacent compromised node.

        You can only move to nodes that are adjacent to your current position
        and where you already have at least USER access.
        """
        position = ctx.attacker.position
        neighbors = ctx.topology.neighbors(position)

        if target_node not in neighbors:
            return (
                f"Failed: {target_node} is not adjacent to {position}. "
                f"Adjacent nodes: {neighbors}"
            )

        access = ctx.attacker.access_levels.get(target_node, AccessLevel.NONE)
        if access == AccessLevel.NONE:
            return (
                f"Failed: no access on {target_node}. "
                f"Compromise it first with execute_technique."
            )

        ctx.attacker.position = target_node
        ctx.attacker.path.append(target_node)

        ctx.actions_this_round.append({
            "action": "move",
            "node_id": target_node,
            "technique_id": "lateral_movement",
        })

        return f"Moved to {target_node}. Current access: {access.value}."

    @tool
    def exfiltrate(node_id: str) -> str:
        """Extract value from a compromised node.

        You must have at least USER access on the node. The node's value is
        added to your total exfiltrated value.
        """
        if node_id not in ctx.topology.nodes:
            return f"Error: node '{node_id}' does not exist."

        access = ctx.attacker.access_levels.get(node_id, AccessLevel.NONE)
        if access == AccessLevel.NONE:
            return f"Failed: no access on {node_id}. Compromise it first."

        attrs = ctx.topology.get_attrs(node_id)
        ctx.attacker.exfiltrated_value += attrs.value

        ctx.actions_this_round.append({
            "action": "exfiltrate",
            "node_id": node_id,
            "technique_id": "T1041",
            "noise": 0.45,
        })

        return (
            f"Exfiltrated {attrs.value:.1f} from {node_id}. "
            f"Total exfiltrated: {ctx.attacker.exfiltrated_value:.1f}"
        )

    return [scan_network, probe_node, execute_technique, move_lateral, exfiltrate]
