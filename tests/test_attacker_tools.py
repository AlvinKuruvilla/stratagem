"""Tests for the 5 attacker tools."""

from stratagem.agents.context import GameContext
from stratagem.agents.tools.attacker_tools import create_attacker_tools
from stratagem.environment.attack_surface import AccessLevel
from stratagem.environment.network import NetworkTopology
from stratagem.game.state import AttackerState, DefenderState, GameState


def _make_state(
    position: str = "web-1",
    budget: float = 10.0,
    access: dict | None = None,
) -> GameState:
    topo = NetworkTopology.small_enterprise()
    attacker = AttackerState(position=position)
    if access:
        attacker.access_levels = access
        for nid in access:
            if access[nid] != AccessLevel.NONE:
                attacker.compromised_nodes.append(nid)
    attacker.path.append(position)
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


def _get_tools(
    position: str = "web-1",
    budget: float = 10.0,
    access: dict | None = None,
    seed: int = 42,
) -> tuple[list, GameContext]:
    state = _make_state(position, budget, access)
    ctx = GameContext.from_game_state(state, seed=seed)
    tools = create_attacker_tools(ctx)
    return tools, ctx


def _tool_by_name(tools, name):
    return next(t for t in tools if t.name == name)


class TestScanNetwork:
    def test_discovers_neighbors(self):
        tools, _ = _get_tools(position="web-1")
        result = _tool_by_name(tools, "scan_network").invoke({})
        # web-1 connects to fw-ext and router-1.
        assert "fw-ext" in result
        assert "router-1" in result

    def test_records_action(self):
        tools, ctx = _get_tools(position="web-1")
        _tool_by_name(tools, "scan_network").invoke({})
        assert len(ctx.actions_this_round) == 1
        assert ctx.actions_this_round[0]["action"] == "scan"

    def test_shows_existing_access(self):
        tools, _ = _get_tools(
            position="router-1",
            access={"router-1": AccessLevel.USER, "ws-1": AccessLevel.USER},
        )
        result = _tool_by_name(tools, "scan_network").invoke({})
        assert "access=user" in result


class TestProbeNode:
    def test_probe_existing_node(self):
        tools, _ = _get_tools(position="web-1")
        result = _tool_by_name(tools, "probe_node").invoke({"node_id": "web-1"})
        assert "web-1" in result
        assert "T1190" in result  # Exploit Public-Facing Application

    def test_probe_nonexistent_node(self):
        tools, _ = _get_tools()
        result = _tool_by_name(tools, "probe_node").invoke({"node_id": "fake"})
        assert "Error" in result

    def test_records_action(self):
        tools, ctx = _get_tools()
        _tool_by_name(tools, "probe_node").invoke({"node_id": "web-1"})
        assert len(ctx.actions_this_round) == 1
        assert ctx.actions_this_round[0]["action"] == "probe"


class TestExecuteTechnique:
    def test_successful_exploit(self):
        # Use a seed that gives a low roll (success).
        # T1190 has 0.35 success rate.  seed=0 → rng.random() ≈ 0.844 (fail).
        # We need to find a seed that works. Let's use seed=100.
        import random

        for s in range(200):
            r = random.Random(s)
            if r.random() <= 0.35:
                good_seed = s
                break

        tools, ctx = _get_tools(position="web-1", seed=good_seed)
        result = _tool_by_name(tools, "execute_technique").invoke({
            "technique_id": "T1190",
            "target_node": "web-1",
        })
        assert "succeeded" in result.lower()
        assert ctx.attacker.access_levels.get("web-1") == AccessLevel.USER

    def test_failed_technique(self):
        # Find a seed that gives a high roll (failure for T1190 @ 0.35).
        import random

        for s in range(200):
            r = random.Random(s)
            if r.random() > 0.35:
                bad_seed = s
                break

        tools, ctx = _get_tools(position="web-1", seed=bad_seed)
        result = _tool_by_name(tools, "execute_technique").invoke({
            "technique_id": "T1190",
            "target_node": "web-1",
        })
        assert "failed" in result.lower()

    def test_insufficient_access(self):
        tools, _ = _get_tools(position="web-1")
        # T1068 requires USER access.
        result = _tool_by_name(tools, "execute_technique").invoke({
            "technique_id": "T1068",
            "target_node": "web-1",
        })
        assert "requires" in result.lower()

    def test_inapplicable_technique(self):
        # T1059.001 (PowerShell) requires Windows with SMB/RDP.
        # web-1 is Linux.
        tools, _ = _get_tools(
            position="web-1",
            access={"web-1": AccessLevel.USER},
        )
        result = _tool_by_name(tools, "execute_technique").invoke({
            "technique_id": "T1059.001",
            "target_node": "web-1",
        })
        assert "not applicable" in result.lower()

    def test_unknown_technique(self):
        tools, _ = _get_tools()
        result = _tool_by_name(tools, "execute_technique").invoke({
            "technique_id": "T9999",
            "target_node": "web-1",
        })
        assert "unknown" in result.lower()

    def test_nonexistent_target(self):
        tools, _ = _get_tools()
        result = _tool_by_name(tools, "execute_technique").invoke({
            "technique_id": "T1190",
            "target_node": "fake",
        })
        assert "Error" in result

    def test_records_action(self):
        tools, ctx = _get_tools(position="web-1", seed=1)
        _tool_by_name(tools, "execute_technique").invoke({
            "technique_id": "T1190",
            "target_node": "web-1",
        })
        assert len(ctx.actions_this_round) == 1
        assert ctx.actions_this_round[0]["technique_id"] == "T1190"


class TestMoveLateral:
    def test_successful_move(self):
        tools, ctx = _get_tools(
            position="web-1",
            access={"web-1": AccessLevel.USER, "router-1": AccessLevel.USER},
        )
        result = _tool_by_name(tools, "move_lateral").invoke({"target_node": "router-1"})
        assert "Moved to router-1" in result
        assert ctx.attacker.position == "router-1"
        assert "router-1" in ctx.attacker.path

    def test_not_adjacent(self):
        tools, ctx = _get_tools(position="web-1")
        result = _tool_by_name(tools, "move_lateral").invoke({"target_node": "db-1"})
        assert "not adjacent" in result.lower()
        assert ctx.attacker.position == "web-1"

    def test_no_access(self):
        tools, ctx = _get_tools(position="web-1")
        result = _tool_by_name(tools, "move_lateral").invoke({"target_node": "router-1"})
        assert "no access" in result.lower()
        assert ctx.attacker.position == "web-1"


class TestExfiltrate:
    def test_successful_exfiltration(self):
        tools, ctx = _get_tools(
            position="db-1",
            access={"db-1": AccessLevel.USER},
        )
        result = _tool_by_name(tools, "exfiltrate").invoke({"node_id": "db-1"})
        assert "9.0" in result  # db-1 has value 9.0
        assert ctx.attacker.exfiltrated_value == 9.0

    def test_no_access(self):
        tools, ctx = _get_tools(position="web-1")
        result = _tool_by_name(tools, "exfiltrate").invoke({"node_id": "db-1"})
        assert "no access" in result.lower()
        assert ctx.attacker.exfiltrated_value == 0.0

    def test_nonexistent_node(self):
        tools, _ = _get_tools()
        result = _tool_by_name(tools, "exfiltrate").invoke({"node_id": "fake"})
        assert "Error" in result

    def test_records_action(self):
        tools, ctx = _get_tools(
            position="db-1",
            access={"db-1": AccessLevel.USER},
        )
        _tool_by_name(tools, "exfiltrate").invoke({"node_id": "db-1"})
        assert len(ctx.actions_this_round) == 1
        assert ctx.actions_this_round[0]["action"] == "exfiltrate"
