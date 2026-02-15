"""FastAPI application for the Stratagem web dashboard."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from stratagem.web.routes import compare, play, solver, topology

app = FastAPI(
    title="Stratagem",
    description="Stackelberg security game equilibrium dashboard",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(topology.router)
app.include_router(solver.router)
app.include_router(compare.router)
app.include_router(play.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
