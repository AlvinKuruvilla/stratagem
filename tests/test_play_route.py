"""Tests for the play mode game runner."""

from __future__ import annotations

import asyncio
import json

import pytest

from stratagem.environment.network import NetworkTopology
from stratagem.web.game_runner import (
    compute_attacker_path,
    run_game_stream,
    strategy_to_defender_actions,
)


@pytest.fixture
def small_topology() -> NetworkTopology:
    return NetworkTopology.small_enterprise()


# ── compute_attacker_path ────────────────────────────────────────────


class TestComputeAttackerPath:
    def test_returns_connected_path(self, small_topology: NetworkTopology):
        entry = small_topology.entry_points()[0]
        path = compute_attacker_path(small_topology, entry)
        assert len(path) >= 2
        assert path[0] == entry

        # Every consecutive pair should be neighbors.
        for i in range(len(path) - 1):
            neighbors = small_topology.neighbors(path[i])
            assert path[i + 1] in neighbors, f"{path[i+1]} not neighbor of {path[i]}"

    def test_targets_highest_value_node(self, small_topology: NetworkTopology):
        entry = small_topology.entry_points()[0]
        path = compute_attacker_path(small_topology, entry)
        target = path[-1]

        # db-2 has value 10.0, highest in small topology.
        assert small_topology.get_attrs(target).value >= 9.0

    def test_entry_only_if_isolated(self):
        """If the entry point has no reachable targets, returns just the entry."""
        from stratagem.environment.network import OS, NodeAttributes, NodeType, Service

        topo = NetworkTopology(name="isolated")
        topo.add_node(
            "entry",
            NodeAttributes(
                NodeType.SERVER, OS.LINUX, [Service.SSH], 1.0, is_entry_point=True
            ),
        )
        path = compute_attacker_path(topo, "entry")
        assert path == ["entry"]


# ── strategy_to_defender_actions ─────────────────────────────────────


class TestStrategyToDefenderActions:
    @pytest.mark.parametrize("strategy", ["sse_optimal", "uniform", "static", "heuristic"])
    def test_produces_valid_actions(self, small_topology: NetworkTopology, strategy: str):
        actions = strategy_to_defender_actions(small_topology, 10.0, strategy)
        assert isinstance(actions, list)

        valid_types = {"honeypot", "decoy_credential", "honeytoken"}
        valid_nodes = set(small_topology.nodes)
        for asset_type, node_id in actions:
            assert asset_type in valid_types, f"Unknown asset type: {asset_type}"
            assert node_id in valid_nodes, f"Unknown node: {node_id}"

    def test_respects_budget(self, small_topology: NetworkTopology):
        from stratagem.environment.deception import ASSET_COSTS, DeceptionType

        actions = strategy_to_defender_actions(small_topology, 5.0, "sse_optimal")
        total_cost = sum(
            ASSET_COSTS[DeceptionType(asset_type)]
            for asset_type, _ in actions
        )
        assert total_cost <= 5.0 + 1e-8

    def test_unknown_strategy_falls_back(self, small_topology: NetworkTopology):
        """Unknown strategy should fallback to sse_optimal without error."""
        actions = strategy_to_defender_actions(small_topology, 10.0, "nonexistent")
        assert isinstance(actions, list)


# ── run_game_stream ──────────────────────────────────────────────────


class TestRunGameStream:
    def test_produces_expected_event_sequence(self, small_topology: NetworkTopology):
        entry = small_topology.entry_points()[0]
        path = compute_attacker_path(small_topology, entry)
        actions = strategy_to_defender_actions(small_topology, 10.0, "sse_optimal")

        events: list[tuple[str, dict]] = []

        async def collect():
            async for chunk in run_game_stream(
                topology=small_topology,
                budget=10.0,
                max_rounds=3,
                seed=42,
                defender_actions=actions,
                attacker_path=path,
            ):
                # Parse SSE chunk.
                for block in chunk.strip().split("\n\n"):
                    if not block.strip():
                        continue
                    event_type = "message"
                    data_str = ""
                    for line in block.split("\n"):
                        if line.startswith("event: "):
                            event_type = line[7:].strip()
                        elif line.startswith("data: "):
                            data_str = line[6:]
                    if data_str:
                        events.append((event_type, json.loads(data_str)))

        asyncio.run(collect())

        # Must start with game_start and defender_setup.
        event_types = [e[0] for e in events]
        assert event_types[0] == "game_start"
        assert event_types[1] == "defender_setup"

        # Must end with game_end.
        assert event_types[-1] == "game_end"

        # Must have at least one round cycle.
        assert "round_start" in event_types
        assert "attacker_action" in event_types
        assert "round_result" in event_types

    def test_game_end_has_winner(self, small_topology: NetworkTopology):
        entry = small_topology.entry_points()[0]
        path = compute_attacker_path(small_topology, entry)
        actions = strategy_to_defender_actions(small_topology, 10.0, "static")

        last_event: dict = {}

        async def collect():
            nonlocal last_event
            async for chunk in run_game_stream(
                topology=small_topology,
                budget=10.0,
                max_rounds=5,
                seed=42,
                defender_actions=actions,
                attacker_path=path,
            ):
                for block in chunk.strip().split("\n\n"):
                    if not block.strip():
                        continue
                    for line in block.split("\n"):
                        if line.startswith("data: "):
                            last_event = json.loads(line[6:])

        asyncio.run(collect())

        assert "winner" in last_event
        assert last_event["winner"] in ("attacker", "defender")
