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
│           │  Evaluation     │                        │
│           │  Engine         │                        │
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
pip install -e ".[dev]"
```

```bash
# Run a single game with default topology
stratagem run --topology small --rounds 50

# Benchmark against baselines
stratagem benchmark --topology medium --trials 100

# Launch the evaluation dashboard
stratagem dashboard
```

## Project Structure

```
stratagem/
├── src/stratagem/
│   ├── agents/
│   │   ├── defender.py        # Defender agent (leader)
│   │   └── attacker.py        # Attacker agent (follower)
│   ├── game/
│   │   ├── state.py           # Game state representation
│   │   ├── graph.py           # LangGraph orchestration
│   │   └── solver.py          # Stackelberg equilibrium solver
│   ├── environment/
│   │   ├── network.py         # Simulated network topology
│   │   ├── deception.py       # Honeypots, decoys, fake credentials
│   │   └── attack_surface.py  # MITRE ATT&CK action space
│   ├── evaluation/
│   │   ├── metrics.py         # Detection rate, cost, dwell time
│   │   ├── baselines.py       # Static/random/heuristic baselines
│   │   └── dashboard.py       # Results visualization
│   └── cli.py                 # CLI entrypoint
├── configs/
│   └── topologies/            # Network topology definitions
├── tests/
├── pyproject.toml
└── README.md
```

## How It Works

1. **Environment Setup** — A network topology is loaded with nodes (servers, workstations, databases) and edges (network connections). Each node has properties like OS, services, and value to the defender.

2. **Defender Commits** — The defender agent analyzes the network and commits to a mixed strategy: probability distributions over where to place honeypots, decoy credentials, and fake services. The Stackelberg solver computes the optimal mixed strategy.

3. **Attacker Responds** — The attacker agent observes the defense posture (with configurable partial observability) and plans an optimal attack path through the network using MITRE ATT&CK techniques as its action space.

4. **Evaluation** — The game runs for N rounds. Detection events, attacker dwell time, and defender resource usage are logged. Results are compared against static and random baselines.

## License

MIT
