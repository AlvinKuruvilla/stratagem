"""Comparison route: SSE vs all baselines."""

from __future__ import annotations

from fastapi import APIRouter

from stratagem.evaluation.baselines import (
    heuristic_baseline,
    static_baseline,
    uniform_baseline,
)
from stratagem.game.solver import UtilityParams, solve_stackelberg
from stratagem.web.converters import solution_to_response
from stratagem.web.routes.topology import _get_topology
from stratagem.web.schemas import CompareResponse, SolveRequest

router = APIRouter(prefix="/api", tags=["compare"])


@router.post("/compare", response_model=CompareResponse)
def compare(req: SolveRequest) -> CompareResponse:
    """Run SSE + all 3 baselines and return all 4 solutions."""
    topo = _get_topology(req.topology)
    params = UtilityParams(alpha=req.alpha, beta=req.beta)

    sse_sol = solve_stackelberg(topo, req.budget, params)
    uni_sol = uniform_baseline(topo, req.budget, params)
    sta_sol = static_baseline(topo, req.budget, params)
    heu_sol = heuristic_baseline(topo, req.budget, params)

    return CompareResponse(
        sse=solution_to_response(sse_sol, topo, req.budget, params),
        uniform=solution_to_response(uni_sol, topo, req.budget, params),
        static=solution_to_response(sta_sol, topo, req.budget, params),
        heuristic=solution_to_response(heu_sol, topo, req.budget, params),
    )
