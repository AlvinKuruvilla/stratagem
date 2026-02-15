"""SSE solver route."""

from __future__ import annotations

from fastapi import APIRouter

from stratagem.game.solver import UtilityParams, solve_stackelberg
from stratagem.web.converters import solution_to_response
from stratagem.web.routes.topology import _get_topology
from stratagem.web.schemas import SolveRequest, SolutionResponse

router = APIRouter(prefix="/api", tags=["solver"])


@router.post("/solve", response_model=SolutionResponse)
def solve(req: SolveRequest) -> SolutionResponse:
    """Run the Stackelberg equilibrium solver and return the solution."""
    topo = _get_topology(req.topology)
    params = UtilityParams(alpha=req.alpha, beta=req.beta)
    solution = solve_stackelberg(topo, req.budget, params)
    return solution_to_response(solution, topo, req.budget, params)
