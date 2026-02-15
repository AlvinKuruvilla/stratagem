"""LangGraph game loop: defender setup → attacker turns → evaluate → loop/end."""

from __future__ import annotations

from typing import Callable, Literal

from langgraph.graph import END, START, StateGraph

from stratagem.agents.attacker import create_attacker_node
from stratagem.agents.defender import create_defender_node
from stratagem.environment.attack_surface import AccessLevel
from stratagem.environment.network import NetworkTopology
from stratagem.game.state import AttackerState, DefenderState, DetectionEvent, GameState


def evaluate_round(state: GameState) -> dict:
    """Process attacker actions against defender's deception assets.

    For each attacker action on a node where deception assets are deployed,
    roll detection probability. Create DetectionEvent on hit. Then check
    win conditions.
    """
    defender = DefenderState.from_dict(state["defender"])
    attacker = AttackerState.from_dict(state["attacker"])
    detections = [DetectionEvent.from_dict(d) for d in state.get("detections", [])]
    actions = state.get("actions_log", [])
    current_round = state["current_round"]

    import random

    rng = random.Random(current_round)  # Deterministic per round.

    for action in actions:
        node_id = action.get("node_id", "")
        technique_id = action.get("technique_id", "")
        noise = action.get("noise", 0.3)

        assets_on_node = defender.assets_on_node(node_id)
        for asset in assets_on_node:
            if asset.triggered:
                continue
            detection_roll = min(asset.detection_probability * (1 + noise), 1.0)
            if rng.random() < detection_roll:
                asset.triggered = True
                attacker.detected = True
                detections.append(
                    DetectionEvent(
                        round=current_round,
                        node_id=node_id,
                        asset_type=asset.asset_type.value,
                        technique_id=technique_id,
                    )
                )

    # Advance round counter.
    next_round = current_round + 1

    # Determine win conditions.
    game_over = False
    winner = ""

    if attacker.detected:
        game_over = True
        winner = "defender"
    elif next_round > state["max_rounds"]:
        game_over = True
        # Attacker survives all rounds — whoever has more utility wins.
        if attacker.exfiltrated_value > 0:
            winner = "attacker"
        else:
            winner = "defender"

    return {
        "attacker": attacker.to_dict(),
        "defender": defender.to_dict(),
        "detections": [d.to_dict() for d in detections],
        "actions_log": [],  # Clear for next round.
        "current_round": next_round,
        "game_over": game_over,
        "winner": winner,
    }


def should_continue(state: GameState) -> Literal["continue", "end"]:
    """Route: loop back to attacker_turn or end the game."""
    if state.get("game_over", False):
        return "end"
    return "continue"


def build_game_graph(
    defender_node: Callable | None = None,
    attacker_node: Callable | None = None,
    **llm_kwargs,
) -> StateGraph:
    """Build the game StateGraph.

    Accepts optional custom nodes for testing with stubs. If not provided,
    creates LLM-powered nodes using the given llm_kwargs.
    """
    if defender_node is None:
        defender_node = create_defender_node(**llm_kwargs)
    if attacker_node is None:
        attacker_node = create_attacker_node(**llm_kwargs)

    graph = StateGraph(GameState)

    graph.add_node("defender_setup", defender_node)
    graph.add_node("attacker_turn", attacker_node)
    graph.add_node("evaluate_round", evaluate_round)

    graph.add_edge(START, "defender_setup")
    graph.add_edge("defender_setup", "attacker_turn")
    graph.add_edge("attacker_turn", "evaluate_round")

    graph.add_conditional_edges(
        "evaluate_round",
        should_continue,
        {"continue": "attacker_turn", "end": END},
    )

    return graph


def create_initial_state(
    topology: NetworkTopology,
    budget: float,
    max_rounds: int,
    entry_point: str | None = None,
    seed: int | None = None,
) -> GameState:
    """Create the initial GameState for a new game.

    If no entry_point is specified, uses the first entry point in the topology.
    """
    entry_points = topology.entry_points()
    if not entry_points:
        raise ValueError("Topology has no entry points.")

    if entry_point is None:
        entry_point = entry_points[0]
    elif entry_point not in entry_points:
        raise ValueError(f"'{entry_point}' is not an entry point. Available: {entry_points}")

    attacker = AttackerState(position=entry_point)
    attacker.path.append(entry_point)
    attacker.access_levels[entry_point] = AccessLevel.NONE

    defender = DefenderState(budget=budget)

    return {
        "messages": [],
        "topology": topology.to_dict(),
        "attacker": attacker.to_dict(),
        "defender": defender.to_dict(),
        "detections": [],
        "actions_log": [],
        "current_round": 1,
        "max_rounds": max_rounds,
        "game_over": False,
        "winner": "",
    }
