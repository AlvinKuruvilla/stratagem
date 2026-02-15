"""Tests for the deception assets module."""

from stratagem.environment.deception import (
    ASSET_COSTS,
    DeceptionAsset,
    DeceptionType,
    decoy_credential,
    honeytoken,
    honeypot,
)
from stratagem.environment.network import Service


class TestDeceptionAssets:
    def test_honeypot_creation(self):
        hp = honeypot("web-1", Service.HTTP)
        assert hp.asset_type == DeceptionType.HONEYPOT
        assert hp.node_id == "web-1"
        assert hp.detection_probability == 0.85
        assert hp.cost == 3.0
        assert hp.triggered is False

    def test_decoy_credential_creation(self):
        dc = decoy_credential("ws-1")
        assert dc.asset_type == DeceptionType.DECOY_CREDENTIAL
        assert dc.detection_probability == 0.70

    def test_honeytoken_creation(self):
        ht = honeytoken("db-1")
        assert ht.asset_type == DeceptionType.HONEYTOKEN
        assert ht.detection_probability == 0.50

    def test_cost_ordering(self):
        """Honeypots should be most expensive, honeytokens cheapest."""
        assert ASSET_COSTS[DeceptionType.HONEYPOT] > ASSET_COSTS[DeceptionType.DECOY_CREDENTIAL]
        assert ASSET_COSTS[DeceptionType.DECOY_CREDENTIAL] > ASSET_COSTS[DeceptionType.HONEYTOKEN]

    def test_serialization_roundtrip(self):
        hp = honeypot("web-1", Service.HTTP)
        restored = DeceptionAsset.from_dict(hp.to_dict())
        assert restored.asset_type == hp.asset_type
        assert restored.node_id == hp.node_id
        assert restored.detection_probability == hp.detection_probability
        assert restored.cost == hp.cost
