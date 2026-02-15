"""Tests for the network topology module."""

from stratagem.environment.network import (
    NetworkTopology,
    NodeAttributes,
    NodeType,
    OS,
    Service,
)


class TestNodeAttributes:
    def test_roundtrip_serialization(self):
        attrs = NodeAttributes(
            node_type=NodeType.SERVER,
            os=OS.LINUX,
            services=[Service.HTTP, Service.SSH],
            value=5.0,
            is_entry_point=True,
        )
        restored = NodeAttributes.from_dict(attrs.to_dict())
        assert restored.node_type == attrs.node_type
        assert restored.os == attrs.os
        assert restored.services == attrs.services
        assert restored.value == attrs.value
        assert restored.is_entry_point == attrs.is_entry_point
        assert restored.compromised is False


class TestNetworkTopology:
    def test_add_node_and_query(self):
        topo = NetworkTopology(name="test")
        attrs = NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.SSH], 5.0)
        topo.add_node("srv-1", attrs)
        assert topo.node_count == 1
        assert topo.get_attrs("srv-1").node_type == NodeType.SERVER

    def test_add_edge_and_neighbors(self):
        topo = NetworkTopology(name="test")
        topo.add_node("a", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.SSH], 1.0))
        topo.add_node("b", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.SSH], 1.0))
        topo.add_edge("a", "b", segment="lan")
        assert "b" in topo.neighbors("a")
        assert "a" in topo.neighbors("b")

    def test_entry_points(self):
        topo = NetworkTopology(name="test")
        topo.add_node("ext", NodeAttributes(NodeType.FIREWALL, OS.LINUX, [Service.DNS], 1.0, is_entry_point=True))
        topo.add_node("int", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.SSH], 5.0))
        assert topo.entry_points() == ["ext"]

    def test_high_value_targets(self):
        topo = NetworkTopology(name="test")
        topo.add_node("low", NodeAttributes(NodeType.WORKSTATION, OS.WINDOWS, [Service.RDP], 2.0))
        topo.add_node("high", NodeAttributes(NodeType.DATABASE, OS.LINUX, [Service.MYSQL], 10.0))
        hvt = topo.high_value_targets(threshold=8.0)
        assert "high" in hvt
        assert "low" not in hvt

    def test_compromised_tracking(self):
        topo = NetworkTopology(name="test")
        topo.add_node("srv", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.SSH], 5.0))
        assert topo.compromised_nodes() == []
        topo.set_compromised("srv")
        assert "srv" in topo.compromised_nodes()

    def test_dict_roundtrip(self):
        topo = NetworkTopology.small_enterprise()
        data = topo.to_dict()
        restored = NetworkTopology.from_dict(data)
        assert restored.node_count == topo.node_count
        assert restored.name == topo.name
        assert len(restored.entry_points()) == len(topo.entry_points())


class TestFactoryTopologies:
    def test_small_enterprise(self):
        topo = NetworkTopology.small_enterprise()
        assert topo.node_count == 10
        assert len(topo.entry_points()) >= 1
        assert len(topo.high_value_targets()) >= 1

    def test_medium_enterprise(self):
        topo = NetworkTopology.medium_enterprise()
        assert topo.node_count == 21
        assert len(topo.entry_points()) >= 1

    def test_large_enterprise(self):
        topo = NetworkTopology.large_enterprise()
        assert topo.node_count == 43
        assert len(topo.entry_points()) >= 1

    def test_all_topologies_are_connected(self):
        """Every factory topology should be a single connected component."""
        for factory in [
            NetworkTopology.small_enterprise,
            NetworkTopology.medium_enterprise,
            NetworkTopology.large_enterprise,
        ]:
            topo = factory()
            import networkx as nx

            assert nx.is_connected(topo.graph), f"{topo.name} is not connected"


class TestYamlLoading:
    def test_load_small_yaml(self, tmp_path):
        topo = NetworkTopology.small_enterprise()
        yaml_path = tmp_path / "test.yaml"
        import yaml

        with open(yaml_path, "w") as f:
            yaml.dump(topo.to_dict(), f)
        loaded = NetworkTopology.from_yaml(yaml_path)
        assert loaded.node_count == topo.node_count
        assert loaded.name == topo.name
