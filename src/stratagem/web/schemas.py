"""Pydantic request/response models for the Stratagem web API."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class SolveRequest(BaseModel):
    topology: str = Field(default="small", description="Topology preset (small/medium/large)")
    budget: float = Field(default=5.0, ge=0, description="Deception budget")
    alpha: float = Field(default=1.0, ge=0, description="Defender detection reward scale")
    beta: float = Field(default=1.0, ge=0, description="Attacker detection penalty scale")


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class NodeInfo(BaseModel):
    id: str
    node_type: str
    os: str
    services: list[str]
    value: float
    is_entry_point: bool


class EdgeInfo(BaseModel):
    source: str
    target: str
    segment: str


class TopologyStats(BaseModel):
    name: str
    node_count: int
    edge_count: int
    entry_points: int
    high_value_targets: int


class TopologyResponse(BaseModel):
    name: str
    nodes: list[NodeInfo]
    edges: list[EdgeInfo]


class NodeUtilityBreakdown(BaseModel):
    node_id: str
    value: float
    detection_probability: float
    coverage: dict[str, float]  # asset_type → probability
    is_entry_point: bool
    # Utility terms
    defender_covered_utility: float  # U_d^c(t) = α·v(t)
    defender_uncovered_utility: float  # U_d^u(t) = -v(t)
    attacker_covered_utility: float  # U_a^c(t) = -β·v(t)
    attacker_uncovered_utility: float  # U_a^u(t) = v(t)
    # Expected utilities at this node
    defender_expected_utility: float
    attacker_expected_utility: float


class SolutionResponse(BaseModel):
    topology_name: str
    budget: float
    alpha: float
    beta: float
    attacker_target: str
    defender_expected_utility: float
    attacker_expected_utility: float
    node_breakdowns: list[NodeUtilityBreakdown]


class CompareResponse(BaseModel):
    sse: SolutionResponse
    uniform: SolutionResponse
    static: SolutionResponse
    heuristic: SolutionResponse
