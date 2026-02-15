"""Tests for the game state module."""

from stratagem.environment.attack_surface import AccessLevel
from stratagem.environment.deception import honeypot
from stratagem.environment.network import Service
from stratagem.game.state import AttackerState, DefenderState, DetectionEvent


class TestAttackerState:
    def test_initial_state(self):
        attacker = AttackerState(position="web-1")
        assert attacker.position == "web-1"
        assert attacker.exfiltrated_value == 0.0
        assert attacker.detected is False
        assert attacker.path == []

    def test_access_level_check(self):
        attacker = AttackerState(position="web-1")
        attacker.access_levels["web-1"] = AccessLevel.USER
        assert attacker.has_access("web-1", AccessLevel.USER)
        assert not attacker.has_access("web-1", AccessLevel.ROOT)

    def test_root_satisfies_user_check(self):
        attacker = AttackerState(position="web-1")
        attacker.access_levels["web-1"] = AccessLevel.ROOT
        assert attacker.has_access("web-1", AccessLevel.USER)
        assert attacker.has_access("web-1", AccessLevel.ROOT)

    def test_no_access_by_default(self):
        attacker = AttackerState(position="web-1")
        assert not attacker.has_access("db-1", AccessLevel.USER)

    def test_serialization(self):
        attacker = AttackerState(position="web-1")
        attacker.access_levels["web-1"] = AccessLevel.USER
        attacker.path = ["fw-ext", "web-1"]
        data = attacker.to_dict()
        assert data["position"] == "web-1"
        assert data["access_levels"]["web-1"] == "user"


class TestDefenderState:
    def test_budget_tracking(self):
        defender = DefenderState(budget=10.0)
        hp = honeypot("web-1", Service.HTTP)
        assert defender.can_afford(hp.cost)
        assert defender.deploy(hp)
        assert defender.remaining_budget == 7.0

    def test_cannot_exceed_budget(self):
        defender = DefenderState(budget=2.0)
        hp = honeypot("web-1", Service.HTTP)  # costs 3.0
        assert not defender.can_afford(hp.cost)
        assert not defender.deploy(hp)
        assert defender.remaining_budget == 2.0

    def test_assets_on_node(self):
        defender = DefenderState(budget=20.0)
        defender.deploy(honeypot("web-1", Service.HTTP))
        defender.deploy(honeypot("web-2", Service.HTTP))
        assert len(defender.assets_on_node("web-1")) == 1
        assert len(defender.assets_on_node("web-2")) == 1
        assert len(defender.assets_on_node("db-1")) == 0


class TestDetectionEvent:
    def test_creation_and_serialization(self):
        event = DetectionEvent(
            round=5, node_id="web-1", asset_type="honeypot", technique_id="T1190"
        )
        data = event.to_dict()
        assert data["round"] == 5
        assert data["node_id"] == "web-1"
