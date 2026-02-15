# Stratagem — Implementation Plan

## Phase 1: Foundation ✅

> **Status:** Complete — 38/38 tests passing, CLI functional.

### 1.1 Project Scaffolding ✅
- `pyproject.toml` with deps: `langgraph`, `langchain-openai`, `scipy`, `networkx`, `typer`, `rich`, `pyyaml`
- `src/stratagem/` package layout with `agents/`, `game/`, `environment/`, `evaluation/` subpackages
- `ruff` for linting, `pytest` for testing
- CLI skeleton with `typer` — `stratagem run`, `benchmark`, `dashboard`, `topology list/show`

### 1.2 Network Environment ✅
- **`environment/network.py`** — `NetworkTopology` class on `networkx.Graph`
  - `NodeAttributes` with `node_type`, `os`, `services`, `value`, `compromised`, `is_entry_point`
  - 5 node types (`server`, `workstation`, `database`, `router`, `firewall`), 2 OS options, 9 service types
  - Factory topologies: `small_enterprise()` (10 nodes), `medium_enterprise()` (21 nodes), `large_enterprise()` (43 nodes)
  - YAML serialization/deserialization, `configs/topologies/small.yaml` as reference
  - Query helpers: `entry_points()`, `high_value_targets()`, `compromised_nodes()`, `neighbors()`
- **`environment/attack_surface.py`** — MITRE ATT&CK action space
  - 18 curated techniques across 9 tactics (initial access through exfiltration)
  - Each technique: `id`, `name`, `tactic`, `base_success_rate`, `noise`, `required_access`, `grants_access`, `required_services`, `supported_os`
  - `get_applicable_techniques(node, access_level)` filters by OS, services, and access
  - `TECHNIQUE_BY_ID` index for fast lookup
- **`environment/deception.py`** — Deception assets
  - 3 types: `Honeypot` (det: 0.85, cost: 3.0), `DecoyCredential` (det: 0.70, cost: 1.5), `HoneyToken` (det: 0.50, cost: 1.0)
  - Factory functions: `honeypot()`, `decoy_credential()`, `honeytoken()`
  - `ASSET_COSTS` and `ASSET_DETECTION_PROBS` dicts for solver/budget calculations

### 1.3 Game State ✅
- **`game/state.py`** — LangGraph-compatible state
  - `GameState(MessagesState)` TypedDict with `topology`, `attacker`, `defender`, `detections`, `current_round`, `max_rounds`, `game_over`, `winner`
  - `AttackerState` dataclass: position, access levels per node, path history, compromised nodes, exfiltrated value, detected flag
  - `DefenderState` dataclass: budget tracking, deployed assets list, `deploy()` with budget enforcement, `assets_on_node()` query
  - `DetectionEvent` dataclass: round, node, asset type, technique ID

### 1.4 Tests ✅
- 38 tests across 4 test files:
  - `test_network.py` — serialization roundtrip, topology structure, factory node counts, connectivity, YAML loading
  - `test_attack_surface.py` — catalog integrity, OS/service filtering, access level gating, tactic grouping
  - `test_deception.py` — asset creation, cost ordering, serialization
  - `test_game_state.py` — attacker access checks, defender budget enforcement, detection events

---

## Phase 2: Game Theory Core ✅

> **Status:** Complete — 75/75 tests passing, SSE solver + 3 baselines functional.

### 2.1 Stackelberg Solver (`src/stratagem/game/solver.py`) ✅
- **Multiple LPs** formulation (one LP per candidate attacker target)
- Strong Stackelberg Equilibrium via `scipy.optimize.linprog`
- Heterogeneous resource model (ERASER-style)
- Utility model: U_d^c(t) = α·v(t), U_d^u(t) = −v(t), U_a^c(t) = −β·v(t), U_a^u(t) = v(t)
- Output: defender mixed strategy, attacker best-response target, detection probabilities per node

### 2.2 Baselines (`src/stratagem/evaluation/baselines.py`) ✅
- `UniformRandomBaseline` — spreads budget evenly across nodes
- `StaticBaseline` — greedily covers highest-value nodes
- `HeuristicBaseline` — covers highest degree-centrality nodes
- All return `StackelbergSolution` for fair comparison

---

## Phase 2.5: Web Dashboard ✅

> **Status:** Complete — FastAPI backend + React 19 frontend with SaaS-polished UI.

### Backend (`src/stratagem/web/`)  ✅
- FastAPI with 3 routes: `/api/solve`, `/api/compare`, `/api/topologies`
- CORS configured for localhost:5173
- Pydantic request/response schemas

### Frontend (`frontend/src/`) ✅
- React 19 + TypeScript + Vite + Tailwind CSS v4
- Network graph (React Flow + dagre layout) with coverage heatmap and **graph legend**
- Budget/alpha/beta sliders with live debounced re-solving
- Node detail panel with KaTeX math rendering of utility formulas
- Charts: attacker EU per node, defender EU comparison, per-node detection probability (Recharts)
- Zustand state management
- Design system: Inter + JetBrains Mono fonts, surface/border tokens, custom form controls

---

## Phase 3: LangGraph Agents ⬅️ NEXT

### 3.1 Defender Agent (`src/stratagem/agents/defender.py`)
- LangGraph node wrapping an LLM (GPT-4o or Claude)
- System prompt encodes the defender's role: analyze network topology, reason about high-value targets, decide deception placement
- **Tools available to the defender:**
  - `inspect_topology()` — view network nodes and edges
  - `get_node_value(node_id)` — check value of a specific node
  - `get_budget()` — check remaining budget
  - `deploy_honeypot(node_id)` — place a honeypot
  - `deploy_decoy_credential(node_id)` — plant a decoy credential
  - `deploy_honeytoken(node_id)` — plant a honeytoken
  - `get_solver_recommendation()` — query the Stackelberg solver for the mathematically optimal mixed strategy
- The agent can choose to follow or deviate from the solver recommendation (this is where the LLM reasoning adds value — it can incorporate contextual reasoning the solver can't)

### 3.2 Attacker Agent (`src/stratagem/agents/attacker.py`)
- LangGraph node wrapping an LLM
- System prompt encodes the attacker's role: find and compromise high-value targets while avoiding detection
- **Tools available to the attacker:**
  - `scan_network()` — discover visible nodes (partial observability: some honeypots are hidden)
  - `probe_node(node_id)` — check services/OS on a node (risk of detection)
  - `execute_technique(technique_id, target_node)` — attempt a MITRE ATT&CK technique
  - `move_lateral(target_node)` — move to an adjacent compromised node
  - `exfiltrate(node_id)` — attempt to extract value from a compromised node
- Attacker has **partial observability**: can observe some defender deployments but not all (configurable)

### 3.3 LangGraph Orchestration (`src/stratagem/game/graph.py`)
- Game graph structure:
  ```
  START → defender_turn → attacker_turn → evaluate_round → {continue | END}
  ```
- `defender_turn`: Defender agent takes actions (deploy deception assets)
- `attacker_turn`: Attacker agent takes actions (move, scan, attack)
- `evaluate_round`: Check for detections, update state, increment round
- Conditional edge: if `round < max_rounds` and attacker not caught → continue; else → END
- State is passed through the graph as `GameState`

---

## Phase 4: Evaluation & Metrics

### 4.1 Metrics Engine (`src/stratagem/evaluation/metrics.py`)
- **Attacker Detection Rate** — % of games where attacker was detected before reaching goal
- **Mean Time to Detect** — average round at which first detection occurs
- **Defender Cost Efficiency** — detection rate per unit of budget spent
- **Attacker Dwell Time** — rounds attacker spends in the network before detection or goal completion
- **Defender Utility** — cumulative game-theoretic utility across trials
- All metrics computed over N trial runs with confidence intervals

### 4.2 Benchmark Runner
- Run Stackelberg-optimal strategy vs. all baselines on each topology size
- Record per-trial results to JSON/CSV
- Statistical significance tests (Mann-Whitney U) for metric comparisons

### 4.3 Dashboard (`src/stratagem/evaluation/dashboard.py`)
- `rich`-based terminal dashboard showing:
  - Metric comparison table (Stackelberg vs baselines)
  - Per-round detection timeline
  - Network topology visualization (ASCII or simple)

---

## Phase 5: CLI & Polish

### 5.1 CLI (`src/stratagem/cli.py`)
- Wire `stratagem run` to the game engine (Phase 3)
- Wire `stratagem benchmark` to the benchmark runner (Phase 4)
- Wire `stratagem dashboard` to the dashboard (Phase 4)
- `stratagem topology list` ✅ and `stratagem topology show <name>` ✅ already functional

### 5.2 Testing
- Unit tests for solver (verify equilibrium properties)
- ~~Unit tests for environment (topology generation, attack mechanics)~~ ✅ Done
- Integration test for full game loop (defender → attacker → evaluate)
- Baseline sanity checks (Stackelberg should weakly dominate random)

---

## Implementation Order

```
Phase 1 ✅ → Phase 2 ✅ → Phase 2.5 ✅ → 3.3 → 3.1 → 3.2 → 4.1 → 4.2 → 4.3 → 5.1 → 5.2
                                           ^^^
                                         YOU ARE HERE
```

## Resume Bullet Target

> Built a multi-agent Stackelberg security game framework using LangGraph, modeling attacker-defender interactions over simulated enterprise networks with MITRE ATT&CK techniques — Stackelberg-optimal deception placement achieved **X% higher detection rate** and **Y% lower mean time-to-detect** vs. static baselines across 1,000+ simulated engagements.
