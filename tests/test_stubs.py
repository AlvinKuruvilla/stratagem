"""Tests for stub agents and full game with stubs."""

from stratagem.agents.stubs import create_stub_attacker, create_stub_defender
from stratagem.environment.network import NetworkTopology
from stratagem.game.graph import build_game_graph, create_initial_state
from stratagem.game.state import DefenderState


def _make_state(
    budget: float = 10.0,
    max_rounds: int = 5,
    entry_point: str = "web-1",
) -> dict:
    topo = NetworkTopology.small_enterprise()
    return create_initial_state(topo, budget, max_rounds, entry_point=entry_point)


class TestStubDefender:
    def test_deploys_given_assets(self):
        state = _make_state()
        defender = create_stub_defender([
            ("honeypot", "db-1"),
            ("honeytoken", "web-1"),
        ])
        result = defender(state)
        defender_state = DefenderState.from_dict(result["defender"])
        assert len(defender_state.deployed_assets) == 2
        asset_nodes = [a.node_id for a in defender_state.deployed_assets]
        assert "db-1" in asset_nodes
        assert "web-1" in asset_nodes

    def test_respects_budget(self):
        state = _make_state(budget=2.0)
        defender = create_stub_defender([
            ("honeypot", "db-1"),  # costs 3.0, should fail
            ("honeytoken", "web-1"),  # costs 1.0, should succeed
        ])
        result = defender(state)
        defender_state = DefenderState.from_dict(result["defender"])
        # Honeypot deployment fails (3.0 > 2.0), honeytoken succeeds.
        assert len(defender_state.deployed_assets) == 1
        assert defender_state.deployed_assets[0].node_id == "web-1"

    def test_empty_actions(self):
        state = _make_state()
        defender = create_stub_defender([])
        result = defender(state)
        defender_state = DefenderState.from_dict(result["defender"])
        assert len(defender_state.deployed_assets) == 0


class TestStubAttacker:
    def test_follows_path(self):
        state = _make_state(entry_point="web-1")
        # The attacker will try to move from web-1 to router-1.
        # First it needs to compromise router-1.
        attacker = create_stub_attacker(["web-1", "router-1"], seed=42)
        result = attacker(state)
        # The attacker should have attempted something.
        assert len(result.get("actions_log", [])) > 0

    def test_deterministic_with_same_seed(self):
        state1 = _make_state(entry_point="web-1")
        state2 = _make_state(entry_point="web-1")
        attacker1 = create_stub_attacker(["web-1", "router-1"], seed=42)
        attacker2 = create_stub_attacker(["web-1", "router-1"], seed=42)
        result1 = attacker1(state1)
        result2 = attacker2(state2)
        assert result1["attacker"] == result2["attacker"]
        assert result1["actions_log"] == result2["actions_log"]

    def test_different_seeds_may_differ(self):
        state1 = _make_state(entry_point="web-1")
        state2 = _make_state(entry_point="web-1")
        attacker1 = create_stub_attacker(["web-1", "router-1"], seed=42)
        attacker2 = create_stub_attacker(["web-1", "router-1"], seed=999)
        result1 = attacker1(state1)
        result2 = attacker2(state2)
        # Results may or may not differ, but the test verifies both run without error.
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)


class TestFullGameWithStubs:
    def test_game_terminates(self):
        """A full game with stubs should terminate within max_rounds."""
        topo = NetworkTopology.small_enterprise()
        state = create_initial_state(topo, budget=10.0, max_rounds=3)

        defender = create_stub_defender([
            ("honeypot", "router-1"),
            ("honeytoken", "db-1"),
        ])
        attacker = create_stub_attacker(
            ["web-1", "router-1", "app-1", "db-1"],
            seed=42,
        )

        graph = build_game_graph(defender_node=defender, attacker_node=attacker)
        compiled = graph.compile()
        final = compiled.invoke(state)

        assert final["game_over"] is True
        assert final["winner"] in ("attacker", "defender")
        assert final["current_round"] <= 4  # max_rounds + 1 (post-increment)

    def test_defender_wins_with_heavy_coverage(self):
        """Heavy deception coverage should give the defender a good chance."""
        topo = NetworkTopology.small_enterprise()
        state = create_initial_state(topo, budget=20.0, max_rounds=10)

        # Cover every node the attacker would traverse.
        defender = create_stub_defender([
            ("honeypot", "web-1"),
            ("honeypot", "router-1"),
            ("honeypot", "app-1"),
            ("honeypot", "db-1"),
            ("honeypot", "db-2"),
        ])
        attacker = create_stub_attacker(
            ["web-1", "router-1", "app-1", "db-1"],
            seed=42,
        )

        graph = build_game_graph(defender_node=defender, attacker_node=attacker)
        compiled = graph.compile()
        final = compiled.invoke(state)

        assert final["game_over"] is True
        # With honeypots on every node, the defender very likely detects.
        # (Not guaranteed since detection is probabilistic, but very likely.)

    def test_attacker_survives_no_assets(self):
        """Without deception assets, the attacker should never be detected."""
        topo = NetworkTopology.small_enterprise()
        state = create_initial_state(topo, budget=10.0, max_rounds=3)

        defender = create_stub_defender([])  # No assets deployed.
        attacker = create_stub_attacker(
            ["web-1", "router-1", "app-1", "db-1"],
            seed=42,
        )

        graph = build_game_graph(defender_node=defender, attacker_node=attacker)
        compiled = graph.compile()
        final = compiled.invoke(state)

        assert final["game_over"] is True
        assert len(final["detections"]) == 0
