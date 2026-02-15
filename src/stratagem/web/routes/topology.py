"""Topology listing and detail routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from stratagem.environment.network import NetworkTopology
from stratagem.web.schemas import EdgeInfo, NodeInfo, TopologyResponse, TopologyStats

router = APIRouter(prefix="/api/topologies", tags=["topologies"])

_PRESETS = {
    "small": NetworkTopology.small_enterprise,
    "medium": NetworkTopology.medium_enterprise,
    "large": NetworkTopology.large_enterprise,
}


def _get_topology(name: str) -> NetworkTopology:
    factory = _PRESETS.get(name)
    if factory is None:
        raise HTTPException(status_code=404, detail=f"Unknown topology: {name}")
    return factory()


@router.get("", response_model=list[TopologyStats])
def list_topologies() -> list[TopologyStats]:
    """List available topologies with basic stats."""
    results: list[TopologyStats] = []
    for preset_name, factory in _PRESETS.items():
        topo = factory()
        results.append(
            TopologyStats(
                name=preset_name,
                node_count=topo.node_count,
                edge_count=topo.graph.number_of_edges(),
                entry_points=len(topo.entry_points()),
                high_value_targets=len(topo.high_value_targets()),
            )
        )
    return results


@router.get("/{name}", response_model=TopologyResponse)
def get_topology(name: str) -> TopologyResponse:
    """Get full topology details (nodes + edges)."""
    topo = _get_topology(name)

    nodes = []
    for nid in topo.nodes:
        attrs = topo.get_attrs(nid)
        nodes.append(
            NodeInfo(
                id=nid,
                node_type=attrs.node_type.value,
                os=attrs.os.value,
                services=[s.value for s in attrs.services],
                value=attrs.value,
                is_entry_point=attrs.is_entry_point,
            )
        )

    edges = []
    for src, dst, data in topo.graph.edges(data=True):
        edges.append(
            EdgeInfo(
                source=src,
                target=dst,
                segment=data.get("segment", "default"),
            )
        )

    return TopologyResponse(name=topo.name, nodes=nodes, edges=edges)
