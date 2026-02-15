"""Bridge between game agents and SSE event stream for the Play mode."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator

import networkx as nx

from stratagem.agents.stubs import create_stub_attacker, create_stub_defender
from stratagem.environment.deception import ASSET_COSTS
from stratagem.environment.network import NetworkTopology
from stratagem.evaluation.baselines import heuristic_baseline, static_baseline, uniform_baseline
from stratagem.game.graph import create_initial_state, evaluate_round
from stratagem.game.solver import StackelbergSolution, UtilityParams, solve_stackelberg
from stratagem.game.state import AttackerState, DefenderState, DetectionEvent


def _sse(event: str, data: dict) -> str:
    """Format a Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# ── Mapping solver coverage → deterministic defender actions ──────────


def strategy_to_defender_actions(
    topology: NetworkTopology,
    budget: float,
    strategy: str,
) -> list[tuple[str, str]]:
    """Convert a solver/baseline strategy into concrete (asset_type, node_id) pairs.

    For each node in the solution's coverage, if any asset has coverage > 0.5
    we deploy it (within the original budget).
    """
    params = UtilityParams()

    solvers: dict[str, callable] = {
        "sse_optimal": lambda: solve_stackelberg(topology, budget, params),
        "uniform": lambda: uniform_baseline(topology, budget, params),
        "static": lambda: static_baseline(topology, budget, params),
        "heuristic": lambda: heuristic_baseline(topology, budget, params),
    }

    solver_fn = solvers.get(strategy)
    if solver_fn is None:
        solver_fn = solvers["sse_optimal"]

    solution: StackelbergSolution = solver_fn()

    actions: list[tuple[str, str]] = []
    remaining = budget

    for node_id, assets in solution.coverage.items():
        for asset_type, prob in assets.items():
            if prob > 0.5:
                cost = ASSET_COSTS[asset_type]
                if cost <= remaining + 1e-8:
                    actions.append((asset_type.value, node_id))
                    remaining -= cost

    return actions


# ── Compute attacker path using shortest path to highest-value target ─


def compute_attacker_path(topology: NetworkTopology, entry_point: str) -> list[str]:
    """Find a connected path from the entry point to the highest-value target."""
    hvts = topology.high_value_targets(threshold=0.0)
    if not hvts:
        return [entry_point]

    # Sort by value descending.
    hvts.sort(key=lambda nid: topology.get_attrs(nid).value, reverse=True)

    for target in hvts:
        if target == entry_point:
            continue
        try:
            path = nx.shortest_path(topology.graph, entry_point, target)
            return path
        except nx.NetworkXNoPath:
            continue

    return [entry_point]


# ── SSE game stream ──────────────────────────────────────────────────


async def run_game_stream(
    topology: NetworkTopology,
    budget: float,
    max_rounds: int,
    seed: int,
    defender_actions: list[tuple[str, str]],
    attacker_path: list[str],
) -> AsyncGenerator[str, None]:
    """Run a game step-by-step, yielding SSE events between phases."""
    entry_point = attacker_path[0] if attacker_path else topology.entry_points()[0]

    # Create stub agents.
    defender_node = create_stub_defender(defender_actions)
    attacker_node = create_stub_attacker(attacker_path, seed=seed)

    # Create initial game state.
    state = create_initial_state(topology, budget, max_rounds, entry_point=entry_point, seed=seed)

    # ── game_start ──
    yield _sse("game_start", {
        "topology_name": topology.name,
        "max_rounds": max_rounds,
        "budget": budget,
        "attacker_entry": entry_point,
        "seed": seed,
    })
    await asyncio.sleep(0.3)

    # ── defender_setup ──
    update = defender_node(state)
    state = {**state, **update}

    defender_state = DefenderState.from_dict(state["defender"])
    deployed = [
        {
            "asset_type": a.asset_type.value,
            "node_id": a.node_id,
            "detection_probability": a.detection_probability,
            "cost": a.cost,
        }
        for a in defender_state.deployed_assets
    ]

    yield _sse("defender_setup", {
        "deployed_assets": deployed,
        "total_spent": defender_state.total_spent,
        "remaining_budget": defender_state.remaining_budget,
    })
    await asyncio.sleep(0.5)

    # ── Round loop ──
    for round_num in range(1, max_rounds + 1):
        attacker_pre = AttackerState.from_dict(state["attacker"])

        yield _sse("round_start", {
            "round": round_num,
            "attacker_position": attacker_pre.position,
            "compromised_nodes": attacker_pre.compromised_nodes,
            "attacker_path": attacker_pre.path,
        })
        await asyncio.sleep(0.3)

        # Attacker acts.
        update = attacker_node(state)
        state = {**state, **update}

        attacker_post = AttackerState.from_dict(state["attacker"])
        actions_log = state.get("actions_log", [])

        action_events = []
        for action in actions_log:
            action_events.append({
                "action": action.get("action", ""),
                "node_id": action.get("node_id", ""),
                "technique_id": action.get("technique_id", ""),
                "success": True,
                "value": 0,
            })

        yield _sse("attacker_action", {
            "round": round_num,
            "actions": action_events,
            "new_position": attacker_post.position,
            "compromised_nodes": attacker_post.compromised_nodes,
            "exfiltrated_value": attacker_post.exfiltrated_value,
        })
        await asyncio.sleep(0.5)

        # Evaluate round (detection, win conditions).
        update = evaluate_round(state)
        state = {**state, **update}

        detections = [DetectionEvent.from_dict(d) for d in state.get("detections", [])]
        new_detections = [d for d in detections if d.round == round_num]

        game_over = state.get("game_over", False)
        winner = state.get("winner", "")

        yield _sse("round_result", {
            "round": round_num,
            "detections": [
                {
                    "node_id": d.node_id,
                    "asset_type": d.asset_type,
                    "technique_id": d.technique_id,
                }
                for d in new_detections
            ],
            "attacker_detected": AttackerState.from_dict(state["attacker"]).detected,
            "game_over": game_over,
            "winner": winner,
        })
        await asyncio.sleep(0.5)

        if game_over:
            break

    # ── game_end ──
    final_attacker = AttackerState.from_dict(state["attacker"])
    all_detections = [DetectionEvent.from_dict(d) for d in state.get("detections", [])]

    yield _sse("game_end", {
        "winner": state.get("winner", ""),
        "rounds_played": state["current_round"] - 1,
        "total_detections": len(all_detections),
        "attacker_exfiltrated": final_attacker.exfiltrated_value,
        "attacker_path": final_attacker.path,
        "compromised_nodes": final_attacker.compromised_nodes,
    })
