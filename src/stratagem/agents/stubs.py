"""Deterministic stub agents for testing without LLMs."""

from __future__ import annotations

from typing import Callable

from stratagem.agents.context import GameContext
from stratagem.environment.attack_surface import (
    AccessLevel,
    get_applicable_techniques,
)
from stratagem.environment.deception import decoy_credential, honeypot, honeytoken
from stratagem.environment.network import Service
from stratagem.game.state import GameState

# Maps asset type name to factory function.
_ASSET_FACTORIES = {
    "honeypot": lambda nid: honeypot(nid, Service.HTTP),
    "decoy_credential": decoy_credential,
    "honeytoken": honeytoken,
}


def create_stub_defender(
    actions: list[tuple[str, str]],
) -> Callable[[GameState], dict]:
    """Create a stub defender that deploys a fixed list of assets.

    Args:
        actions: List of (asset_type, node_id) tuples. asset_type is one of
            "honeypot", "decoy_credential", "honeytoken".

    Returns:
        A node function with the same signature as an LLM-powered defender.
    """

    def stub_defender(state: GameState) -> dict:
        ctx = GameContext.from_game_state(state)
        for asset_type, node_id in actions:
            factory = _ASSET_FACTORIES[asset_type]
            asset = factory(node_id)
            ctx.defender.deploy(asset)
        return ctx.to_state_update()

    return stub_defender


def create_stub_attacker(
    path: list[str],
    seed: int = 42,
) -> Callable[[GameState], dict]:
    """Create a stub attacker that follows a fixed node path.

    At each step, the attacker:
    1. If not on the next target node, tries to move laterally (if access exists)
       or executes the highest-success-rate applicable technique.
    2. If on a node with value, attempts to exfiltrate.

    Args:
        path: Ordered list of node IDs to visit.
        seed: RNG seed for deterministic technique rolls.

    Returns:
        A node function with the same signature as an LLM-powered attacker.
    """

    def stub_attacker(state: GameState) -> dict:
        ctx = GameContext.from_game_state(state, seed=seed)
        position = ctx.attacker.position

        for target in path:
            if target == position:
                continue

            # Check if target is a neighbor.
            neighbors = ctx.topology.neighbors(position)
            if target not in neighbors:
                continue

            access = ctx.attacker.access_levels.get(target, AccessLevel.NONE)

            if access == AccessLevel.NONE:
                # Try to compromise the target node.
                attrs = ctx.topology.get_attrs(target)
                current_access = ctx.attacker.access_levels.get(target, AccessLevel.NONE)
                techniques = get_applicable_techniques(attrs, current_access)

                if not techniques:
                    continue

                # Pick highest success rate technique.
                best = max(techniques, key=lambda t: t.base_success_rate)

                # Roll for success.
                roll = ctx.rng.random()
                if roll <= best.base_success_rate:
                    # Upgrade access.
                    access_order = [AccessLevel.NONE, AccessLevel.USER, AccessLevel.ROOT]
                    current_rank = access_order.index(
                        ctx.attacker.access_levels.get(target, AccessLevel.NONE)
                    )
                    granted_rank = access_order.index(best.grants_access)
                    if granted_rank > current_rank:
                        ctx.attacker.access_levels[target] = best.grants_access

                    if target not in ctx.attacker.compromised_nodes:
                        ctx.attacker.compromised_nodes.append(target)
                        ctx.topology.set_compromised(target)

                ctx.actions_this_round.append({
                    "action": "execute",
                    "node_id": target,
                    "technique_id": best.id,
                    "noise": best.noise,
                })

                access = ctx.attacker.access_levels.get(target, AccessLevel.NONE)

            # Move if we have access.
            if access != AccessLevel.NONE:
                ctx.attacker.position = target
                ctx.attacker.path.append(target)
                position = target

                ctx.actions_this_round.append({
                    "action": "move",
                    "node_id": target,
                    "technique_id": "lateral_movement",
                })

                # Exfiltrate if node has value.
                attrs = ctx.topology.get_attrs(target)
                if attrs.value > 0:
                    ctx.attacker.exfiltrated_value += attrs.value
                    ctx.actions_this_round.append({
                        "action": "exfiltrate",
                        "node_id": target,
                        "technique_id": "T1041",
                        "noise": 0.45,
                    })

            break  # One step per round.

        return ctx.to_state_update()

    return stub_attacker
