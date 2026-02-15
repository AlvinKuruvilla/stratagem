"""Tests for the 7 defender tools."""

from stratagem.agents.context import GameContext
from stratagem.agents.tools.defender_tools import create_defender_tools
from stratagem.environment.network import NetworkTopology
from stratagem.game.state import AttackerState, DefenderState, GameState


def _make_state(budget: float = 10.0) -> GameState:
    """Create a minimal GameState for testing defender tools."""
    topo = NetworkTopology.small_enterprise()
    attacker = AttackerState(position="web-1")
    defender = DefenderState(budget=budget)
    return {
        "messages": [],
        "topology": topo.to_dict(),
        "attacker": attacker.to_dict(),
        "defender": defender.to_dict(),
        "detections": [],
        "actions_log": [],
        "current_round": 1,
        "max_rounds": 10,
        "game_over": False,
        "winner": "",
    }


def _get_tools(budget: float = 10.0) -> tuple[list, GameContext]:
    state = _make_state(budget)
    ctx = GameContext.from_game_state(state)
    tools = create_defender_tools(ctx)
    return tools, ctx


def _tool_by_name(tools, name):
    return next(t for t in tools if t.name == name)


class TestInspectTopology:
    def test_returns_nodes_and_edges(self):
        tools, _ = _get_tools()
        result = _tool_by_name(tools, "inspect_topology").invoke({})
        assert "web-1" in result
        assert "db-1" in result
        assert "<->" in result

    def test_shows_entry_points(self):
        tools, _ = _get_tools()
        result = _tool_by_name(tools, "inspect_topology").invoke({})
        assert "[ENTRY]" in result


class TestGetNodeValue:
    def test_existing_node(self):
        tools, _ = _get_tools()
        result = _tool_by_name(tools, "get_node_value").invoke({"node_id": "db-1"})
        assert "db-1" in result
        assert "9.0" in result

    def test_nonexistent_node(self):
        tools, _ = _get_tools()
        result = _tool_by_name(tools, "get_node_value").invoke({"node_id": "fake-node"})
        assert "Error" in result


class TestGetBudget:
    def test_initial_budget(self):
        tools, _ = _get_tools(budget=10.0)
        result = _tool_by_name(tools, "get_budget").invoke({})
        assert "10.0" in result
        assert "remaining" in result


class TestDeployHoneypot:
    def test_successful_deployment(self):
        tools, ctx = _get_tools(budget=10.0)
        result = _tool_by_name(tools, "deploy_honeypot").invoke({"node_id": "db-1"})
        assert "deployed" in result.lower()
        assert ctx.defender.remaining_budget == 7.0
        assert len(ctx.defender.assets_on_node("db-1")) == 1

    def test_insufficient_budget(self):
        tools, ctx = _get_tools(budget=2.0)
        result = _tool_by_name(tools, "deploy_honeypot").invoke({"node_id": "db-1"})
        assert "Failed" in result
        assert len(ctx.defender.deployed_assets) == 0

    def test_nonexistent_node(self):
        tools, _ = _get_tools()
        result = _tool_by_name(tools, "deploy_honeypot").invoke({"node_id": "fake"})
        assert "Error" in result


class TestDeployDecoyCredential:
    def test_successful_deployment(self):
        tools, ctx = _get_tools(budget=10.0)
        result = _tool_by_name(tools, "deploy_decoy_credential").invoke({"node_id": "web-1"})
        assert "deployed" in result.lower()
        assert ctx.defender.remaining_budget == 8.5

    def test_insufficient_budget(self):
        tools, _ = _get_tools(budget=1.0)
        result = _tool_by_name(tools, "deploy_decoy_credential").invoke({"node_id": "web-1"})
        assert "Failed" in result


class TestDeployHoneytoken:
    def test_successful_deployment(self):
        tools, ctx = _get_tools(budget=10.0)
        result = _tool_by_name(tools, "deploy_honeytoken").invoke({"node_id": "ws-1"})
        assert "deployed" in result.lower()
        assert ctx.defender.remaining_budget == 9.0

    def test_insufficient_budget(self):
        tools, _ = _get_tools(budget=0.5)
        result = _tool_by_name(tools, "deploy_honeytoken").invoke({"node_id": "ws-1"})
        assert "Failed" in result


class TestGetSolverRecommendation:
    def test_returns_recommendation(self):
        tools, _ = _get_tools(budget=10.0)
        result = _tool_by_name(tools, "get_solver_recommendation").invoke({})
        assert "Attacker target" in result
        assert "Defender EU" in result


class TestMultipleDeployments:
    def test_budget_tracks_across_deployments(self):
        tools, ctx = _get_tools(budget=5.5)
        _tool_by_name(tools, "deploy_honeypot").invoke({"node_id": "db-1"})
        assert ctx.defender.remaining_budget == 2.5
        _tool_by_name(tools, "deploy_decoy_credential").invoke({"node_id": "db-2"})
        assert ctx.defender.remaining_budget == 1.0
        _tool_by_name(tools, "deploy_honeytoken").invoke({"node_id": "web-1"})
        assert ctx.defender.remaining_budget == 0.0
        # No more budget.
        result = _tool_by_name(tools, "deploy_honeytoken").invoke({"node_id": "web-2"})
        assert "Failed" in result
