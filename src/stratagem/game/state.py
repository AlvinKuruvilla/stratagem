"""Game state representation for the LangGraph orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Self

from langgraph.graph import MessagesState

from stratagem.environment.attack_surface import AccessLevel
from stratagem.environment.deception import DeceptionAsset


@dataclass
class DetectionEvent:
    """Record of a defender detecting the attacker."""

    round: int
    node_id: str
    asset_type: str  # Which deception asset triggered.
    technique_id: str  # What the attacker was doing when caught.

    def to_dict(self) -> dict:
        return {
            "round": self.round,
            "node_id": self.node_id,
            "asset_type": self.asset_type,
            "technique_id": self.technique_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
            round=data["round"],
            node_id=data["node_id"],
            asset_type=data["asset_type"],
            technique_id=data["technique_id"],
        )


@dataclass
class AttackerState:
    """Tracks the attacker's progress through the network."""

    position: str  # Current node ID.
    access_levels: dict[str, AccessLevel] = field(default_factory=dict)
    path: list[str] = field(default_factory=list)
    compromised_nodes: list[str] = field(default_factory=list)
    exfiltrated_value: float = 0.0
    detected: bool = False

    def has_access(self, node_id: str, minimum: AccessLevel = AccessLevel.USER) -> bool:
        order = [AccessLevel.NONE, AccessLevel.USER, AccessLevel.ROOT]
        current = self.access_levels.get(node_id, AccessLevel.NONE)
        return order.index(current) >= order.index(minimum)

    def to_dict(self) -> dict:
        return {
            "position": self.position,
            "access_levels": {k: v.value for k, v in self.access_levels.items()},
            "path": self.path,
            "compromised_nodes": self.compromised_nodes,
            "exfiltrated_value": self.exfiltrated_value,
            "detected": self.detected,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
            position=data["position"],
            access_levels={k: AccessLevel(v) for k, v in data.get("access_levels", {}).items()},
            path=list(data.get("path", [])),
            compromised_nodes=list(data.get("compromised_nodes", [])),
            exfiltrated_value=float(data.get("exfiltrated_value", 0.0)),
            detected=bool(data.get("detected", False)),
        )


@dataclass
class DefenderState:
    """Tracks the defender's deployed assets and budget."""

    budget: float
    deployed_assets: list[DeceptionAsset] = field(default_factory=list)
    total_spent: float = 0.0

    @property
    def remaining_budget(self) -> float:
        return self.budget - self.total_spent

    def can_afford(self, cost: float) -> bool:
        return self.remaining_budget >= cost

    def deploy(self, asset: DeceptionAsset) -> bool:
        if not self.can_afford(asset.cost):
            return False
        self.deployed_assets.append(asset)
        self.total_spent += asset.cost
        return True

    def assets_on_node(self, node_id: str) -> list[DeceptionAsset]:
        return [a for a in self.deployed_assets if a.node_id == node_id]

    def to_dict(self) -> dict:
        return {
            "budget": self.budget,
            "deployed_assets": [a.to_dict() for a in self.deployed_assets],
            "total_spent": self.total_spent,
            "remaining_budget": self.remaining_budget,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        defender = cls(
            budget=float(data["budget"]),
            total_spent=float(data.get("total_spent", 0.0)),
        )
        for asset_data in data.get("deployed_assets", []):
            defender.deployed_assets.append(DeceptionAsset.from_dict(asset_data))
        return defender


class GameState(MessagesState):
    """Full game state passed through the LangGraph graph.

    Extends MessagesState so agents get the message history automatically.
    Additional fields carry the simulation state.
    """

    # Topology is serialized to dict for state transport.
    topology: dict
    attacker: dict
    defender: dict
    detections: list[dict]
    actions_log: list[dict]  # Attacker actions this round, for detection processing.
    current_round: int
    max_rounds: int
    game_over: bool
    winner: str  # "defender", "attacker", or "" if ongoing.
