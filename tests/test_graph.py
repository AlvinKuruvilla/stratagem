"""Tests for the LangGraph game loop."""

from stratagem.agents.stubs import create_stub_attacker, create_stub_defender
from stratagem.environment.network import NetworkTopology
from stratagem.game.graph import (
    build_game_graph,
    create_initial_state,
    evaluate_round,
    should_continue,
)
from stratagem.game.state import AttackerState, DefenderState


def _make_state(
    budget: float = 10.0,
    max_rounds: int = 5,
    current_round: int = 1,
    game_over: bool = False,
    winner: str = "",
) -> dict:
    topo = NetworkTopology.small_enterprise()
    attacker = AttackerState(position="web-1")
    attacker.path.append("web-1")
    defender = DefenderState(budget=budget)
    return {
        "messages": [],
        "topology": topo.to_dict(),
        "attacker": attacker.to_dict(),
        "defender": defender.to_dict(),
        "detections": [],
        "actions_log": [],
        "current_round": current_round,
        "max_rounds": max_rounds,
        "game_over": game_over,
        "winner": winner,
    }


class TestCreateInitialState:
    def test_basic_creation(self):
        topo = NetworkTopology.small_enterprise()
        state = create_initial_state(topo, budget=10.0, max_rounds=5)
        assert state["current_round"] == 1
        assert state["max_rounds"] == 5
        assert state["game_over"] is False
        assert state["winner"] == ""
        assert state["attacker"]["position"] in [ep for ep in topo.entry_points()]

    def test_custom_entry_point(self):
        topo = NetworkTopology.small_enterprise()
        state = create_initial_state(topo, budget=10.0, max_rounds=5, entry_point="web-2")
        assert state["attacker"]["position"] == "web-2"

    def test_invalid_entry_point(self):
        topo = NetworkTopology.small_enterprise()
        try:
            create_initial_state(topo, budget=10.0, max_rounds=5, entry_point="db-1")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_no_entry_points(self):
        from stratagem.environment.network import OS, NodeAttributes, NodeType, Service

        topo = NetworkTopology(name="empty")
        topo.add_node("n1", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.SSH], 5.0))
        try:
            create_initial_state(topo, budget=10.0, max_rounds=5)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


class TestEvaluateRound:
    def test_no_detection_without_assets(self):
        state = _make_state()
        state["actions_log"] = [
            {"action": "execute", "node_id": "web-1", "technique_id": "T1190", "noise": 0.4}
        ]
        result = evaluate_round(state)
        assert result["attacker"]["detected"] is False
        assert len(result["detections"]) == 0
        assert result["current_round"] == 2

    def test_detection_with_honeypot(self):
        from stratagem.environment.deception import honeypot
        from stratagem.environment.network import Service

        state = _make_state(budget=10.0)
        # Deploy a honeypot on web-1.
        defender = DefenderState(budget=10.0)
        hp = honeypot("web-1", Service.HTTP)
        defender.deploy(hp)
        state["defender"] = defender.to_dict()

        # Attacker acts on web-1 with high noise.
        state["actions_log"] = [
            {"action": "execute", "node_id": "web-1", "technique_id": "T1110", "noise": 0.7}
        ]

        # With honeypot (0.85) * (1 + 0.7) = 1.445, capped at 1.0 → guaranteed detection
        # (with any RNG roll).
        result = evaluate_round(state)
        assert result["attacker"]["detected"] is True
        assert result["game_over"] is True
        assert result["winner"] == "defender"
        assert len(result["detections"]) == 1

    def test_round_limit_attacker_wins(self):
        state = _make_state(max_rounds=3, current_round=3)
        # Attacker has exfiltrated some value.
        attacker = AttackerState(position="web-1", exfiltrated_value=5.0)
        state["attacker"] = attacker.to_dict()
        state["actions_log"] = []

        result = evaluate_round(state)
        assert result["game_over"] is True
        assert result["winner"] == "attacker"

    def test_round_limit_defender_wins_no_exfil(self):
        state = _make_state(max_rounds=3, current_round=3)
        state["actions_log"] = []

        result = evaluate_round(state)
        assert result["game_over"] is True
        assert result["winner"] == "defender"

    def test_actions_log_cleared_after_evaluation(self):
        state = _make_state()
        state["actions_log"] = [
            {"action": "scan", "node_id": "web-1", "technique_id": "T1046"}
        ]
        result = evaluate_round(state)
        assert result["actions_log"] == []


class TestShouldContinue:
    def test_continue_when_not_over(self):
        state = _make_state(game_over=False)
        assert should_continue(state) == "continue"

    def test_end_when_over(self):
        state = _make_state(game_over=True, winner="defender")
        assert should_continue(state) == "end"


class TestBuildGameGraph:
    def test_graph_compiles(self):
        defender = create_stub_defender([("honeytoken", "db-1")])
        attacker = create_stub_attacker(["web-1"])
        graph = build_game_graph(defender_node=defender, attacker_node=attacker)
        compiled = graph.compile()
        assert compiled is not None

    def test_graph_nodes(self):
        defender = create_stub_defender([])
        attacker = create_stub_attacker([])
        graph = build_game_graph(defender_node=defender, attacker_node=attacker)
        node_names = set(graph.nodes.keys())
        assert "defender_setup" in node_names
        assert "attacker_turn" in node_names
        assert "evaluate_round" in node_names
