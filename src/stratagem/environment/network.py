"""Simulated network topology for Stackelberg security games."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Self

import networkx as nx
import yaml


class NodeType(str, Enum):
    SERVER = "server"
    WORKSTATION = "workstation"
    DATABASE = "database"
    ROUTER = "router"
    FIREWALL = "firewall"


class OS(str, Enum):
    LINUX = "linux"
    WINDOWS = "windows"


# Services that can run on a node — determines which ATT&CK techniques apply.
class Service(str, Enum):
    SSH = "ssh"
    HTTP = "http"
    HTTPS = "https"
    SMB = "smb"
    RDP = "rdp"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    FTP = "ftp"
    DNS = "dns"


@dataclass
class NodeAttributes:
    node_type: NodeType
    os: OS
    services: list[Service]
    value: float  # Defender utility lost if compromised.
    compromised: bool = False
    is_entry_point: bool = False  # Can the attacker reach this from outside?

    def to_dict(self) -> dict:
        return {
            "node_type": self.node_type.value,
            "os": self.os.value,
            "services": [s.value for s in self.services],
            "value": self.value,
            "compromised": self.compromised,
            "is_entry_point": self.is_entry_point,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
            node_type=NodeType(data["node_type"]),
            os=OS(data["os"]),
            services=[Service(s) for s in data["services"]],
            value=float(data["value"]),
            compromised=data.get("compromised", False),
            is_entry_point=data.get("is_entry_point", False),
        )


@dataclass
class NetworkTopology:
    """Graph-based network topology where nodes are hosts and edges are connections."""

    graph: nx.Graph = field(default_factory=nx.Graph)
    name: str = "unnamed"

    def add_node(self, node_id: str, attrs: NodeAttributes) -> None:
        self.graph.add_node(node_id, **attrs.to_dict())

    def add_edge(self, src: str, dst: str, segment: str = "default") -> None:
        self.graph.add_edge(src, dst, segment=segment)

    def get_attrs(self, node_id: str) -> NodeAttributes:
        return NodeAttributes.from_dict(self.graph.nodes[node_id])

    def neighbors(self, node_id: str) -> list[str]:
        return list(self.graph.neighbors(node_id))

    def entry_points(self) -> list[str]:
        return [n for n in self.graph.nodes if self.graph.nodes[n].get("is_entry_point")]

    def high_value_targets(self, threshold: float = 8.0) -> list[str]:
        return [n for n in self.graph.nodes if self.graph.nodes[n].get("value", 0) >= threshold]

    @property
    def nodes(self) -> list[str]:
        return list(self.graph.nodes)

    @property
    def node_count(self) -> int:
        return self.graph.number_of_nodes()

    def compromised_nodes(self) -> list[str]:
        return [n for n in self.graph.nodes if self.graph.nodes[n].get("compromised")]

    def set_compromised(self, node_id: str, value: bool = True) -> None:
        self.graph.nodes[node_id]["compromised"] = value

    def summary(self) -> str:
        entry = len(self.entry_points())
        hvt = len(self.high_value_targets())
        return (
            f"Topology '{self.name}': {self.node_count} nodes, "
            f"{self.graph.number_of_edges()} edges, "
            f"{entry} entry points, {hvt} high-value targets"
        )

    def to_dict(self) -> dict:
        nodes = {}
        for nid in self.graph.nodes:
            nodes[nid] = dict(self.graph.nodes[nid])
        edges = []
        for src, dst, data in self.graph.edges(data=True):
            edges.append({"src": src, "dst": dst, "segment": data.get("segment", "default")})
        return {"name": self.name, "nodes": nodes, "edges": edges}

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        topo = cls(name=data.get("name", "unnamed"))
        for nid, ndata in data["nodes"].items():
            topo.add_node(nid, NodeAttributes.from_dict(ndata))
        for edge in data["edges"]:
            topo.add_edge(edge["src"], edge["dst"], segment=edge.get("segment", "default"))
        return topo

    @classmethod
    def from_yaml(cls, path: str | Path) -> Self:
        with open(path) as f:
            return cls.from_dict(yaml.safe_load(f))

    # The factory methods below build pre-configured topologies at three scales.
    # Each follows the same layered pattern: DMZ → corporate LAN → internal tiers.

    @classmethod
    def small_enterprise(cls) -> Self:
        """10-node network: DMZ → corporate LAN → database tier."""
        topo = cls(name="small_enterprise")

        # DMZ
        topo.add_node("fw-ext", NodeAttributes(NodeType.FIREWALL, OS.LINUX, [Service.DNS], 2.0, is_entry_point=True))
        topo.add_node("web-1", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.HTTPS, Service.SSH], 4.0, is_entry_point=True))
        topo.add_node("web-2", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.HTTPS, Service.SSH], 4.0, is_entry_point=True))

        # Corporate LAN
        topo.add_node("router-1", NodeAttributes(NodeType.ROUTER, OS.LINUX, [Service.SSH], 3.0))
        topo.add_node("ws-1", NodeAttributes(NodeType.WORKSTATION, OS.WINDOWS, [Service.SMB, Service.RDP], 2.0))
        topo.add_node("ws-2", NodeAttributes(NodeType.WORKSTATION, OS.WINDOWS, [Service.SMB, Service.RDP], 2.0))
        topo.add_node("ws-3", NodeAttributes(NodeType.WORKSTATION, OS.WINDOWS, [Service.SMB, Service.RDP], 2.0))
        topo.add_node("app-1", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.SSH], 6.0))

        # Database tier
        topo.add_node("db-1", NodeAttributes(NodeType.DATABASE, OS.LINUX, [Service.MYSQL, Service.SSH], 9.0))
        topo.add_node("db-2", NodeAttributes(NodeType.DATABASE, OS.LINUX, [Service.POSTGRESQL, Service.SSH], 10.0))

        # DMZ edges
        topo.add_edge("fw-ext", "web-1", segment="dmz")
        topo.add_edge("fw-ext", "web-2", segment="dmz")
        topo.add_edge("web-1", "router-1", segment="dmz-to-lan")
        topo.add_edge("web-2", "router-1", segment="dmz-to-lan")

        # LAN edges
        topo.add_edge("router-1", "ws-1", segment="lan")
        topo.add_edge("router-1", "ws-2", segment="lan")
        topo.add_edge("router-1", "ws-3", segment="lan")
        topo.add_edge("router-1", "app-1", segment="lan")
        topo.add_edge("ws-1", "ws-2", segment="lan")
        topo.add_edge("ws-2", "ws-3", segment="lan")

        # LAN → DB tier
        topo.add_edge("app-1", "db-1", segment="lan-to-db")
        topo.add_edge("app-1", "db-2", segment="lan-to-db")

        return topo

    @classmethod
    def medium_enterprise(cls) -> Self:
        """25-node network: DMZ → corporate LAN → dev zone → database tier."""
        topo = cls(name="medium_enterprise")

        # DMZ (4 nodes)
        topo.add_node("fw-ext", NodeAttributes(NodeType.FIREWALL, OS.LINUX, [Service.DNS], 2.0, is_entry_point=True))
        topo.add_node("lb-1", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.HTTPS], 3.0, is_entry_point=True))
        topo.add_node("web-1", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.HTTPS, Service.SSH], 4.0))
        topo.add_node("web-2", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.HTTPS, Service.SSH], 4.0))

        # Corporate LAN (8 nodes)
        topo.add_node("router-1", NodeAttributes(NodeType.ROUTER, OS.LINUX, [Service.SSH], 3.0))
        topo.add_node("router-2", NodeAttributes(NodeType.ROUTER, OS.LINUX, [Service.SSH], 3.0))
        for i in range(1, 6):
            os = OS.WINDOWS if i <= 3 else OS.LINUX
            services = [Service.SMB, Service.RDP] if os == OS.WINDOWS else [Service.SSH]
            topo.add_node(f"ws-{i}", NodeAttributes(NodeType.WORKSTATION, os, services, 2.0))
        topo.add_node("mail-1", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.HTTPS, Service.SSH], 5.0))

        # Dev zone (6 nodes)
        topo.add_node("fw-dev", NodeAttributes(NodeType.FIREWALL, OS.LINUX, [Service.SSH], 2.0))
        topo.add_node("ci-1", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.SSH], 6.0))
        topo.add_node("dev-1", NodeAttributes(NodeType.WORKSTATION, OS.LINUX, [Service.SSH], 3.0))
        topo.add_node("dev-2", NodeAttributes(NodeType.WORKSTATION, OS.LINUX, [Service.SSH], 3.0))
        topo.add_node("repo-1", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.SSH], 7.0))
        topo.add_node("artifact-1", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.SSH, Service.FTP], 5.0))

        # Database tier (3 nodes)
        topo.add_node("db-1", NodeAttributes(NodeType.DATABASE, OS.LINUX, [Service.MYSQL, Service.SSH], 9.0))
        topo.add_node("db-2", NodeAttributes(NodeType.DATABASE, OS.LINUX, [Service.POSTGRESQL, Service.SSH], 10.0))
        topo.add_node("db-backup", NodeAttributes(NodeType.DATABASE, OS.LINUX, [Service.SSH, Service.FTP], 8.0))

        # DMZ edges
        topo.add_edge("fw-ext", "lb-1", segment="dmz")
        topo.add_edge("lb-1", "web-1", segment="dmz")
        topo.add_edge("lb-1", "web-2", segment="dmz")
        topo.add_edge("web-1", "router-1", segment="dmz-to-lan")
        topo.add_edge("web-2", "router-1", segment="dmz-to-lan")

        # LAN edges
        topo.add_edge("router-1", "router-2", segment="lan")
        topo.add_edge("router-1", "ws-1", segment="lan")
        topo.add_edge("router-1", "ws-2", segment="lan")
        topo.add_edge("router-1", "ws-3", segment="lan")
        topo.add_edge("router-2", "ws-4", segment="lan")
        topo.add_edge("router-2", "ws-5", segment="lan")
        topo.add_edge("router-1", "mail-1", segment="lan")
        topo.add_edge("ws-1", "ws-2", segment="lan")
        topo.add_edge("ws-2", "ws-3", segment="lan")
        topo.add_edge("ws-4", "ws-5", segment="lan")

        # LAN → Dev zone
        topo.add_edge("router-2", "fw-dev", segment="lan-to-dev")
        topo.add_edge("fw-dev", "ci-1", segment="dev")
        topo.add_edge("fw-dev", "dev-1", segment="dev")
        topo.add_edge("fw-dev", "dev-2", segment="dev")
        topo.add_edge("ci-1", "repo-1", segment="dev")
        topo.add_edge("ci-1", "artifact-1", segment="dev")
        topo.add_edge("dev-1", "dev-2", segment="dev")

        # LAN/Dev → DB tier
        topo.add_edge("mail-1", "db-1", segment="lan-to-db")
        topo.add_edge("ci-1", "db-2", segment="dev-to-db")
        topo.add_edge("db-1", "db-backup", segment="db")
        topo.add_edge("db-2", "db-backup", segment="db")

        return topo

    @classmethod
    def large_enterprise(cls) -> Self:
        """50-node network: DMZ → corporate → dev → staging → production DB + executive subnet."""
        topo = cls(name="large_enterprise")

        # DMZ
        topo.add_node("fw-ext-1", NodeAttributes(NodeType.FIREWALL, OS.LINUX, [Service.DNS], 2.0, is_entry_point=True))
        topo.add_node("fw-ext-2", NodeAttributes(NodeType.FIREWALL, OS.LINUX, [Service.DNS], 2.0, is_entry_point=True))
        topo.add_node("lb-1", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.HTTPS], 3.0))
        topo.add_node("web-1", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.HTTPS, Service.SSH], 4.0))
        topo.add_node("web-2", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.HTTPS, Service.SSH], 4.0))

        # Corporate LAN
        topo.add_node("core-rtr", NodeAttributes(NodeType.ROUTER, OS.LINUX, [Service.SSH], 4.0))
        topo.add_node("lan-rtr-1", NodeAttributes(NodeType.ROUTER, OS.LINUX, [Service.SSH], 3.0))
        topo.add_node("lan-rtr-2", NodeAttributes(NodeType.ROUTER, OS.LINUX, [Service.SSH], 3.0))
        for i in range(1, 9):
            os = OS.WINDOWS if i <= 5 else OS.LINUX
            services = [Service.SMB, Service.RDP] if os == OS.WINDOWS else [Service.SSH]
            topo.add_node(f"ws-{i}", NodeAttributes(NodeType.WORKSTATION, os, services, 2.0))
        topo.add_node("mail-1", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.HTTPS, Service.SSH], 5.0))
        topo.add_node("file-1", NodeAttributes(NodeType.SERVER, OS.WINDOWS, [Service.SMB, Service.RDP], 5.0))
        topo.add_node("ad-1", NodeAttributes(NodeType.SERVER, OS.WINDOWS, [Service.SMB, Service.RDP, Service.DNS], 8.0))
        topo.add_node("vpn-1", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.SSH, Service.HTTPS], 6.0))

        # Executive subnet — high-value workstations behind a dedicated router
        topo.add_node("exec-rtr", NodeAttributes(NodeType.ROUTER, OS.LINUX, [Service.SSH], 3.0))
        topo.add_node("exec-ws-1", NodeAttributes(NodeType.WORKSTATION, OS.WINDOWS, [Service.SMB, Service.RDP], 7.0))
        topo.add_node("exec-ws-2", NodeAttributes(NodeType.WORKSTATION, OS.WINDOWS, [Service.SMB, Service.RDP], 7.0))
        topo.add_node("exec-ws-3", NodeAttributes(NodeType.WORKSTATION, OS.WINDOWS, [Service.SMB, Service.RDP], 7.0))

        # Dev zone
        topo.add_node("fw-dev", NodeAttributes(NodeType.FIREWALL, OS.LINUX, [Service.SSH], 2.0))
        topo.add_node("ci-1", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.SSH], 6.0))
        topo.add_node("ci-2", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.SSH], 6.0))
        for i in range(1, 5):
            topo.add_node(f"dev-{i}", NodeAttributes(NodeType.WORKSTATION, OS.LINUX, [Service.SSH], 3.0))
        topo.add_node("repo-1", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.SSH], 7.0))
        topo.add_node("artifact-1", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.SSH, Service.FTP], 5.0))

        # Staging
        topo.add_node("fw-stg", NodeAttributes(NodeType.FIREWALL, OS.LINUX, [Service.SSH], 2.0))
        topo.add_node("stg-app-1", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.SSH], 5.0))
        topo.add_node("stg-app-2", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.SSH], 5.0))
        topo.add_node("stg-db-1", NodeAttributes(NodeType.DATABASE, OS.LINUX, [Service.MYSQL, Service.SSH], 6.0))
        topo.add_node("stg-db-2", NodeAttributes(NodeType.DATABASE, OS.LINUX, [Service.POSTGRESQL, Service.SSH], 6.0))

        # Production DB tier — the crown jewels
        topo.add_node("fw-prod", NodeAttributes(NodeType.FIREWALL, OS.LINUX, [Service.SSH], 3.0))
        topo.add_node("prod-app-1", NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.SSH], 7.0))
        topo.add_node("prod-db-1", NodeAttributes(NodeType.DATABASE, OS.LINUX, [Service.MYSQL, Service.SSH], 10.0))
        topo.add_node("prod-db-2", NodeAttributes(NodeType.DATABASE, OS.LINUX, [Service.POSTGRESQL, Service.SSH], 10.0))
        topo.add_node("prod-backup", NodeAttributes(NodeType.DATABASE, OS.LINUX, [Service.SSH, Service.FTP], 9.0))

        # Edges: DMZ
        topo.add_edge("fw-ext-1", "lb-1", segment="dmz")
        topo.add_edge("fw-ext-2", "lb-1", segment="dmz")
        topo.add_edge("lb-1", "web-1", segment="dmz")
        topo.add_edge("lb-1", "web-2", segment="dmz")
        topo.add_edge("web-1", "core-rtr", segment="dmz-to-lan")
        topo.add_edge("web-2", "core-rtr", segment="dmz-to-lan")

        # Edges: Corporate LAN
        topo.add_edge("core-rtr", "lan-rtr-1", segment="lan")
        topo.add_edge("core-rtr", "lan-rtr-2", segment="lan")
        topo.add_edge("core-rtr", "ad-1", segment="lan")
        topo.add_edge("core-rtr", "vpn-1", segment="lan")
        topo.add_edge("lan-rtr-1", "ws-1", segment="lan")
        topo.add_edge("lan-rtr-1", "ws-2", segment="lan")
        topo.add_edge("lan-rtr-1", "ws-3", segment="lan")
        topo.add_edge("lan-rtr-1", "ws-4", segment="lan")
        topo.add_edge("lan-rtr-1", "mail-1", segment="lan")
        topo.add_edge("lan-rtr-2", "ws-5", segment="lan")
        topo.add_edge("lan-rtr-2", "ws-6", segment="lan")
        topo.add_edge("lan-rtr-2", "ws-7", segment="lan")
        topo.add_edge("lan-rtr-2", "ws-8", segment="lan")
        topo.add_edge("lan-rtr-2", "file-1", segment="lan")
        topo.add_edge("ws-1", "ws-2", segment="lan")
        topo.add_edge("ws-3", "ws-4", segment="lan")
        topo.add_edge("ws-5", "ws-6", segment="lan")
        topo.add_edge("ws-7", "ws-8", segment="lan")

        # Edges: Executive subnet
        topo.add_edge("core-rtr", "exec-rtr", segment="lan-to-exec")
        topo.add_edge("exec-rtr", "exec-ws-1", segment="exec")
        topo.add_edge("exec-rtr", "exec-ws-2", segment="exec")
        topo.add_edge("exec-rtr", "exec-ws-3", segment="exec")

        # Edges: Dev zone
        topo.add_edge("lan-rtr-2", "fw-dev", segment="lan-to-dev")
        topo.add_edge("fw-dev", "ci-1", segment="dev")
        topo.add_edge("fw-dev", "ci-2", segment="dev")
        topo.add_edge("fw-dev", "dev-1", segment="dev")
        topo.add_edge("fw-dev", "dev-2", segment="dev")
        topo.add_edge("ci-1", "dev-3", segment="dev")
        topo.add_edge("ci-2", "dev-4", segment="dev")
        topo.add_edge("ci-1", "repo-1", segment="dev")
        topo.add_edge("ci-2", "artifact-1", segment="dev")
        topo.add_edge("dev-1", "dev-2", segment="dev")
        topo.add_edge("dev-3", "dev-4", segment="dev")

        # Edges: Staging
        topo.add_edge("ci-1", "fw-stg", segment="dev-to-stg")
        topo.add_edge("fw-stg", "stg-app-1", segment="staging")
        topo.add_edge("fw-stg", "stg-app-2", segment="staging")
        topo.add_edge("stg-app-1", "stg-db-1", segment="staging")
        topo.add_edge("stg-app-2", "stg-db-2", segment="staging")

        # Edges: Production
        topo.add_edge("core-rtr", "fw-prod", segment="lan-to-prod")
        topo.add_edge("fw-prod", "prod-app-1", segment="prod")
        topo.add_edge("prod-app-1", "prod-db-1", segment="prod")
        topo.add_edge("prod-app-1", "prod-db-2", segment="prod")
        topo.add_edge("prod-db-1", "prod-backup", segment="prod")
        topo.add_edge("prod-db-2", "prod-backup", segment="prod")

        return topo
