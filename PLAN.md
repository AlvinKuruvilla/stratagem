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

## Phase 3: LangGraph Agents ✅

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

## Phase 4: Evaluation & Metrics ✅

> **Status:** Complete — 174/174 tests passing, benchmark engine + CLI + API + web dashboard functional.

### 4.1 Metrics Engine (`src/stratagem/evaluation/metrics.py`) ✅
- `TrialResult` dataclass capturing per-game outcomes
- `extract_trial_result()` pure function: final game state → metrics
- `compute_metrics()` aggregates trials into `StrategyMetrics` with:
  - **Detection Rate** with Wilson score 95% CI
  - **Mean Time to Detect** (detected trials only)
  - **Cost Efficiency** (detection rate / budget spent)
  - **Attacker Dwell Time**
  - **Defender Utility** (composite score)
  - **Attacker Exfiltration**
- `compare_strategies()` / `compare_all_pairs()` — Mann-Whitney U tests for statistical significance

### 4.2 Benchmark Runner (`src/stratagem/evaluation/benchmark.py`) ✅
- `run_game_sync()` — synchronous fast game runner (same logic as SSE stream, no async/sleep)
- `BenchmarkConfig` / `BenchmarkResult` dataclasses
- `run_benchmark()` orchestrator: sweeps strategies × topologies × N trials with shared attacker paths
- `export_results_json()` / `export_results_csv()` for downstream analysis

### 4.3 Rich Terminal Dashboard (`src/stratagem/evaluation/dashboard.py`) ✅
- Strategy comparison table (Det. Rate, MTTD, Cost Eff., Dwell Time, Utility, Exfil)
- Statistical significance table (Mann-Whitney U, p-values, YES/no badges)
- Summary panel with headline SSE-vs-baseline improvement percentages

### 4.4 CLI Integration ✅
- `stratagem benchmark` with `--topology`, `--trials`, `--max-rounds`, `--budget`, `--seed`, `--output`, `--csv-output`
- Rich progress bar during execution

### 4.5 Web API + Frontend ✅
- `POST /api/benchmark` endpoint with Pydantic request/response models
- React "Bench" mode tab with controls (trials slider, budget, topology checkboxes)
- Recharts grouped bar chart for detection rate, detailed metrics table, significance badges

---

## Phase 5: Run Benchmark & Interpret Results ⬅️ NEXT

> **Why this is next:** Phases 1–4 built the solver, baselines, game engine, and
> evaluation pipeline. The benchmark is ready to run but hasn't been executed yet.
> Running it will fill in the X% and Y% in the resume bullet and reveal whether
> the SSE solver actually dominates the baselines in simulated play — not just in
> theoretical EU, but in empirical detection rate and dwell time. This is the
> payoff for all the infrastructure work.

### 5.1 Run the Benchmark
- `stratagem benchmark --topology all --trials 100 --output results.json --csv-output trials.csv`
- Examine the Rich dashboard output: which strategy wins on each topology?
- Check statistical significance: are the differences real (p < 0.05)?

### 5.2 Interpret & Validate
- **Detection rate:** Does SSE achieve higher detection than all 3 baselines? By how much?
- **MTTD:** Does SSE detect earlier? Is the difference meaningful?
- **Dwell time:** Do attackers spend fewer rounds active under SSE?
- **Exfiltration:** Does SSE reduce total value stolen?
- **Cost efficiency:** Is SSE a better use of budget?
- Check per-topology patterns: does SSE advantage grow with network size?
- Investigate any surprises (e.g., a baseline beating SSE on some metric)

### 5.3 Fill in the Resume Bullet
- Replace X% and Y% with actual numbers from the benchmark
- If results aren't compelling, investigate: are game parameters realistic? Is the attacker stub too simple?

### 5.4 Remaining Polish
- Wire `stratagem run` to the LLM game engine (currently uses stubs)
- Integration test for full game loop (defender → attacker → evaluate)
- `stratagem topology list` ✅ and `stratagem topology show <name>` ✅ already functional
- `stratagem benchmark` ✅ wired and functional
- `stratagem dashboard` ✅ launches FastAPI + Vite

---

## Implementation Order

```
Phase 1 ✅ → Phase 2 ✅ → Phase 2.5 ✅ → Phase 3 ✅ → Phase 4 ✅ → Phase 5
                                                                       ^^^
                                                                  YOU ARE HERE
```

## Resume Bullet Target

> Built a multi-agent Stackelberg security game framework using LangGraph, modeling attacker-defender interactions over simulated enterprise networks with MITRE ATT&CK techniques — Stackelberg-optimal deception placement achieved **X% higher detection rate** and **Y% lower mean time-to-detect** vs. static baselines across 1,000+ simulated engagements.
