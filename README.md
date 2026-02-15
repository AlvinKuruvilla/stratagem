<p align="center">
  <h1 align="center">Stratagem</h1>
  <p align="center">Stackelberg security games powered by autonomous LLM agents</p>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+"></a>
  <a href="https://github.com/langchain-ai/langgraph"><img src="https://img.shields.io/badge/langgraph-0.3+-purple.svg" alt="LangGraph"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://attack.mitre.org/"><img src="https://img.shields.io/badge/MITRE%20ATT%26CK-v16-red.svg" alt="MITRE ATT&CK"></a>
</p>

---

Stratagem is a multi-agent framework that models cyber defense as a **Stackelberg security game**. A defender agent (leader) commits to a mixed strategy over deception deployments — honeypots, decoy credentials, and fake services — on a simulated network. An attacker agent (follower) observes the defense posture and computes an optimal attack path using MITRE ATT&CK techniques. The system solves for Stackelberg equilibrium and benchmarks the resulting defense against static baselines.

Built with [LangGraph](https://github.com/langchain-ai/langgraph) for agent orchestration and [Nash/Stackelberg solvers](https://en.wikipedia.org/wiki/Stackelberg_competition) for equilibrium computation.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   LangGraph Orchestrator             │
│                                                      │
│  ┌──────────────┐   Game State   ┌───────────────┐  │
│  │   Defender    │◄─────────────►│   Attacker     │  │
│  │   Agent       │               │   Agent        │  │
│  │  (Leader)     │               │  (Follower)    │  │
│  └──────┬───────┘               └───────┬────────┘  │
│         │                               │            │
│         ▼                               ▼            │
│  ┌──────────────┐               ┌───────────────┐   │
│  │  Deception   │               │  ATT&CK       │   │
│  │  Toolkit     │               │  Planner      │   │
│  └──────┬───────┘               └───────┬────────┘  │
│         │                               │            │
│         └───────────┬───────────────────┘            │
│                     ▼                                │
│           ┌─────────────────┐                        │
│           │  Stackelberg    │                        │
│           │  Solver         │                        │
│           └────────┬────────┘                        │
│                    ▼                                 │
│           ┌─────────────────┐                        │
│           │  Web Dashboard  │                        │
│           │  + Evaluation   │                        │
│           └─────────────────┘                        │
└─────────────────────────────────────────────────────┘
```

## Key Results

> Benchmarks run on simulated enterprise network topologies (10–43 nodes).

| Metric | Static Baseline | Stratagem | Delta |
|--------|----------------|-----------|-------|
| Attacker Detection Rate | — | — | — |
| Mean Time to Detect (rounds) | — | — | — |
| Defender Cost Efficiency | — | — | — |
| Attacker Dwell Time (rounds) | — | — | — |

*Results populated after benchmarking phase.*

## Quickstart

```bash
git clone https://github.com/AlvinKuruvilla/stratagem.git
cd stratagem
pip install -e ".[web,dev]"
cd frontend && npm install && cd ..
```

Or with [just](https://github.com/casey/just):

```bash
just setup
```

### Run the Dashboard

```bash
# Start backend + frontend together
just dev

# Or separately:
just backend   # FastAPI on http://localhost:8000
just frontend  # Vite on http://localhost:5173
```

Then open http://localhost:5173 to explore equilibrium results interactively.

### Other Commands

```bash
# Run a single game with default topology
stratagem run --topology small --rounds 50

# Benchmark against baselines
stratagem benchmark --topology medium --trials 100

# Run tests
just test

# Lint + typecheck
just ci
```

Run `just` to see all available recipes.

## Project Structure

```
stratagem/
├── src/stratagem/
│   ├── agents/                  # LangGraph agents (Phase 3)
│   ├── game/
│   │   ├── state.py             # Game state representation
│   │   └── solver.py            # Stackelberg equilibrium solver (SSE via LP)
│   ├── environment/
│   │   ├── network.py           # Simulated network topologies (10/25/50 nodes)
│   │   ├── deception.py         # Honeypots, decoy credentials, honeytokens
│   │   └── attack_surface.py    # MITRE ATT&CK technique catalog (20 techniques)
│   ├── evaluation/
│   │   └── baselines.py         # Uniform, static, and heuristic baselines
│   ├── web/
│   │   ├── app.py               # FastAPI application with CORS
│   │   ├── schemas.py           # Pydantic request/response models
│   │   ├── converters.py        # Solution → API response conversion
│   │   └── routes/
│   │       ├── topology.py      # GET /api/topologies, /api/topologies/{name}
│   │       ├── solver.py        # POST /api/solve
│   │       └── compare.py       # POST /api/compare (SSE vs baselines)
│   └── cli.py                   # CLI entrypoint (Typer)
├── frontend/
│   └── src/
│       ├── api/                 # Typed fetch client + TS interfaces
│       ├── state/               # Zustand store
│       └── components/
│           ├── layout/          # AppShell, ControlPanel
│           ├── graph/           # React Flow network graph + dagre layout
│           ├── charts/          # Recharts: attacker EU, defender comparison, coverage
│           ├── panels/          # Node detail panel with KaTeX math rendering
│           └── controls/        # Topology selector, budget slider, param controls
├── configs/topologies/          # Custom YAML topology definitions
├── tests/                       # 75 tests (solver properties, baselines, network)
├── justfile                     # Task runner recipes
├── pyproject.toml
└── README.md
```

## Web Dashboard

The interactive dashboard visualizes Stackelberg equilibrium results:

- **Network Graph** — React Flow visualization with coverage heatmap (green → yellow → red by detection probability). Attacker targets highlighted in gold, entry points shown with dashed borders.
- **Budget Slider** — Drag to adjust the defender's deception budget; the graph and charts re-solve live (~300ms debounce).
- **Indifference Principle** — Horizontal bar chart showing attacker EU per node. The SSE equalizes the top targets (bars align at the equilibrium reference line).
- **Node Detail Panel** — Click any node to see its value, coverage allocation, and full utility formulas rendered with KaTeX.
- **Baseline Comparison** — Toggle to compare SSE against uniform, static (value-based), and heuristic (centrality-based) baselines. Side-by-side charts show defender EU gap and per-node detection probability differences.

**Stack:** React 19, TypeScript, Vite, Tailwind CSS v4, React Flow, Recharts, KaTeX, Zustand.

## How It Works

1. **Environment Setup** — A network topology is loaded with nodes (servers, workstations, databases) and edges (network connections). Each node has properties like OS, services, and value to the defender.

2. **Defender Commits** — The defender agent analyzes the network and commits to a mixed strategy: probability distributions over where to place honeypots, decoy credentials, and honeytokens. The Stackelberg solver computes the optimal mixed strategy via linear programming.

3. **Attacker Responds** — The attacker observes the defense posture and selects the target node that maximizes their expected utility. The SSE ensures this best response is accounted for in the defender's strategy.

4. **Evaluation** — The solution is compared against three baselines (uniform, static, heuristic). The SSE weakly dominates all baselines by construction — it optimizes defender utility subject to the attacker's strategic response.

## License

MIT
