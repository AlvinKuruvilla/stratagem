"""Play mode SSE endpoint — streams a game round-by-round."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from stratagem.web.game_runner import (
    compute_attacker_path,
    run_game_stream,
    strategy_to_defender_actions,
)
from stratagem.web.routes.topology import _get_topology
from stratagem.web.schemas import PlayGameRequest

router = APIRouter(prefix="/api", tags=["play"])


@router.post("/play")
async def play_game(req: PlayGameRequest) -> StreamingResponse:
    """Launch a game and stream SSE events as it unfolds."""
    topology = _get_topology(req.topology)
    entry_point = topology.entry_points()[0]

    defender_actions = strategy_to_defender_actions(topology, req.budget, req.defender_strategy)
    attacker_path = compute_attacker_path(topology, entry_point)

    return StreamingResponse(
        run_game_stream(
            topology=topology,
            budget=req.budget,
            max_rounds=req.max_rounds,
            seed=req.seed,
            defender_actions=defender_actions,
            attacker_path=attacker_path,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
