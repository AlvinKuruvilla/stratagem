"""Deception assets that the defender can deploy on the network."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Self

from stratagem.environment.network import Service


class DeceptionType(str, Enum):
    HONEYPOT = "honeypot"
    DECOY_CREDENTIAL = "decoy_credential"
    HONEYTOKEN = "honeytoken"


@dataclass
class DeceptionAsset:
    asset_type: DeceptionType
    node_id: str  # Node where this asset is deployed.
    detection_probability: float  # 0-1, chance of detecting an attacker who interacts.
    cost: float  # Budget units consumed by deploying this asset.
    triggered: bool = False  # Has an attacker interacted with this?

    def to_dict(self) -> dict:
        return {
            "asset_type": self.asset_type.value,
            "node_id": self.node_id,
            "detection_probability": self.detection_probability,
            "cost": self.cost,
            "triggered": self.triggered,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
            asset_type=DeceptionType(data["asset_type"]),
            node_id=data["node_id"],
            detection_probability=float(data["detection_probability"]),
            cost=float(data["cost"]),
            triggered=data.get("triggered", False),
        )


# ---------------------------------------------------------------------------
# Factory helpers — pre-configured asset templates
# ---------------------------------------------------------------------------

def honeypot(node_id: str, service: Service) -> DeceptionAsset:
    """Deploy a fake service that looks real to an attacker.

    Honeypots have high detection probability since any interaction is suspicious,
    but they are the most expensive to deploy.
    """
    return DeceptionAsset(
        asset_type=DeceptionType.HONEYPOT,
        node_id=node_id,
        detection_probability=0.85,
        cost=3.0,
    )


def decoy_credential(node_id: str) -> DeceptionAsset:
    """Plant a fake credential on a compromised-looking node.

    Medium detection probability — attacker might use the credential, revealing
    their presence. Cheaper than a full honeypot.
    """
    return DeceptionAsset(
        asset_type=DeceptionType.DECOY_CREDENTIAL,
        node_id=node_id,
        detection_probability=0.70,
        cost=1.5,
    )


def honeytoken(node_id: str) -> DeceptionAsset:
    """Place a fake data artifact (document, API key, DB record) on a node.

    Lower detection probability since the attacker may grab it without
    triggering an alert immediately. Cheapest option.
    """
    return DeceptionAsset(
        asset_type=DeceptionType.HONEYTOKEN,
        node_id=node_id,
        detection_probability=0.50,
        cost=1.0,
    )


# Costs indexed by type for the solver / budget calculations.
ASSET_COSTS: dict[DeceptionType, float] = {
    DeceptionType.HONEYPOT: 3.0,
    DeceptionType.DECOY_CREDENTIAL: 1.5,
    DeceptionType.HONEYTOKEN: 1.0,
}

ASSET_DETECTION_PROBS: dict[DeceptionType, float] = {
    DeceptionType.HONEYPOT: 0.85,
    DeceptionType.DECOY_CREDENTIAL: 0.70,
    DeceptionType.HONEYTOKEN: 0.50,
}
