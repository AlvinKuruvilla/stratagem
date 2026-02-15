"""Mutable bridge between dict-based GameState and live domain objects."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Self

from stratagem.environment.network import NetworkTopology
from stratagem.game.state import AttackerState, DefenderState, DetectionEvent, GameState


@dataclass
class GameContext:
    """Live, mutable game context that agent tools operate on.

    Created from a serialized GameState at the start of each agent node,
    then serialized back into a state-update dict when the node finishes.
    """

    topology: NetworkTopology
    attacker: AttackerState
    defender: DefenderState
    detections: list[DetectionEvent]
    current_round: int
    max_rounds: int
    actions_this_round: list[dict] = field(default_factory=list)
    rng: random.Random = field(default_factory=random.Random)

    @classmethod
    def from_game_state(cls, state: GameState, seed: int | None = None) -> Self:
        """Deserialize a GameState dict into live objects."""
        topology = NetworkTopology.from_dict(state["topology"])
        attacker = AttackerState.from_dict(state["attacker"])
        defender = DefenderState.from_dict(state["defender"])
        detections = [DetectionEvent.from_dict(d) for d in state.get("detections", [])]

        rng = random.Random(seed)

        return cls(
            topology=topology,
            attacker=attacker,
            defender=defender,
            detections=detections,
            current_round=state["current_round"],
            max_rounds=state["max_rounds"],
            rng=rng,
        )

    def to_state_update(self) -> dict:
        """Return a dict of GameState fields to merge back into the graph state."""
        return {
            "topology": self.topology.to_dict(),
            "attacker": self.attacker.to_dict(),
            "defender": self.defender.to_dict(),
            "detections": [d.to_dict() for d in self.detections],
            "actions_log": list(self.actions_this_round),
        }
