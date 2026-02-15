/** Zustand store for global dashboard state. */

import { create } from "zustand";
import { api, streamGame } from "../api/client";
import type {
  ActionLogEntry,
  AttackerActionEvent,
  CompareResponse,
  DeployedAsset,
  DefenderSetupEvent,
  Detection,
  GameEndEvent,
  GameStartEvent,
  RoundResultEvent,
  RoundStartEvent,
  SolutionResponse,
  TopologyResponse,
  TopologyStats,
} from "../api/types";

interface PlayState {
  status: "idle" | "running" | "finished";
  budget: number;
  maxRounds: number;
  seed: number;
  defenderStrategy: string;
  currentRound: number;
  attackerPosition: string;
  attackerPath: string[];
  compromisedNodes: string[];
  deployedAssets: DeployedAsset[];
  detections: Detection[];
  exfiltratedValue: number;
  winner: string;
  actionLog: ActionLogEntry[];
}

const initialPlayState: PlayState = {
  status: "idle",
  budget: 10.0,
  maxRounds: 5,
  seed: 42,
  defenderStrategy: "sse_optimal",
  currentRound: 0,
  attackerPosition: "",
  attackerPath: [],
  compromisedNodes: [],
  deployedAssets: [],
  detections: [],
  exfiltratedValue: 0,
  winner: "",
  actionLog: [],
};

interface GameState {
  // Mode
  mode: "solver" | "play";

  // Topology
  topologies: TopologyStats[];
  selectedTopology: string;
  topologyData: TopologyResponse | null;

  // Params
  budget: number;
  alpha: number;
  beta: number;

  // Solution
  solution: SolutionResponse | null;
  comparison: CompareResponse | null;
  showBaselines: boolean;

  // Play mode
  play: PlayState;
  playController: AbortController | null;

  // UI
  selectedNodeId: string | null;
  loading: boolean;
  error: string | null;

  // Actions
  init: () => Promise<void>;
  setMode: (mode: "solver" | "play") => void;
  setTopology: (name: string) => Promise<void>;
  setBudget: (budget: number) => void;
  setAlpha: (alpha: number) => void;
  setBeta: (beta: number) => void;
  setShowBaselines: (show: boolean) => void;
  setSelectedNode: (nodeId: string | null) => void;
  fetchSolution: () => Promise<void>;
  fetchComparison: () => Promise<void>;

  // Play actions
  setPlayBudget: (budget: number) => void;
  setPlayMaxRounds: (maxRounds: number) => void;
  setPlaySeed: (seed: number) => void;
  setPlayDefenderStrategy: (strategy: string) => void;
  startGame: () => void;
  stopGame: () => void;
  handleGameEvent: (eventType: string, data: unknown) => void;
}

export const useGameStore = create<GameState>((set, get) => ({
  mode: "solver",
  topologies: [],
  selectedTopology: "small",
  topologyData: null,
  budget: 5.0,
  alpha: 1.0,
  beta: 1.0,
  solution: null,
  comparison: null,
  showBaselines: false,
  play: { ...initialPlayState },
  playController: null,
  selectedNodeId: null,
  loading: false,
  error: null,

  init: async () => {
    try {
      set({ loading: true, error: null });
      const topologies = await api.listTopologies();
      const topologyData = await api.getTopology("small");
      set({ topologies, topologyData });
      await get().fetchSolution();
    } catch (e) {
      set({ error: (e as Error).message });
    } finally {
      set({ loading: false });
    }
  },

  setMode: (mode) => {
    const prev = get();
    if (prev.playController) {
      prev.playController.abort();
    }
    set({ mode, playController: null, error: null });
  },

  setTopology: async (name: string) => {
    try {
      set({ loading: true, selectedTopology: name, error: null, selectedNodeId: null });
      const topologyData = await api.getTopology(name);
      set({ topologyData });
      await get().fetchSolution();
      if (get().showBaselines) await get().fetchComparison();
    } catch (e) {
      set({ error: (e as Error).message });
    } finally {
      set({ loading: false });
    }
  },

  setBudget: (budget: number) => {
    set({ budget });
  },

  setAlpha: (alpha: number) => {
    set({ alpha });
  },

  setBeta: (beta: number) => {
    set({ beta });
  },

  setShowBaselines: (show: boolean) => {
    set({ showBaselines: show });
    if (show) get().fetchComparison();
  },

  setSelectedNode: (nodeId: string | null) => {
    set({ selectedNodeId: nodeId });
  },

  fetchSolution: async () => {
    const { selectedTopology, budget, alpha, beta } = get();
    try {
      set({ error: null });
      const solution = await api.solve({
        topology: selectedTopology,
        budget,
        alpha,
        beta,
      });
      set({ solution });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  fetchComparison: async () => {
    const { selectedTopology, budget, alpha, beta } = get();
    try {
      set({ error: null });
      const comparison = await api.compare({
        topology: selectedTopology,
        budget,
        alpha,
        beta,
      });
      set({ comparison });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  // Play mode actions

  setPlayBudget: (budget) => {
    set((s) => ({ play: { ...s.play, budget } }));
  },

  setPlayMaxRounds: (maxRounds) => {
    set((s) => ({ play: { ...s.play, maxRounds } }));
  },

  setPlaySeed: (seed) => {
    set((s) => ({ play: { ...s.play, seed } }));
  },

  setPlayDefenderStrategy: (strategy) => {
    set((s) => ({ play: { ...s.play, defenderStrategy: strategy } }));
  },

  startGame: () => {
    const { selectedTopology, play, playController } = get();

    // Abort any in-flight game.
    if (playController) playController.abort();

    // Reset play state.
    set({
      play: {
        ...initialPlayState,
        budget: play.budget,
        maxRounds: play.maxRounds,
        seed: play.seed,
        defenderStrategy: play.defenderStrategy,
        status: "running",
      },
      error: null,
    });

    const controller = streamGame(
      {
        topology: selectedTopology,
        budget: play.budget,
        max_rounds: play.maxRounds,
        seed: play.seed,
        defender_strategy: play.defenderStrategy,
      },
      (eventType, data) => get().handleGameEvent(eventType, data),
      (err) => set({ error: err.message, play: { ...get().play, status: "idle" } }),
    );

    set({ playController: controller });
  },

  stopGame: () => {
    const { playController } = get();
    if (playController) playController.abort();
    set((s) => ({
      playController: null,
      play: { ...s.play, status: "idle" },
    }));
  },

  handleGameEvent: (eventType, data) => {
    set((s) => {
      const play = { ...s.play };
      const log = [...play.actionLog];

      switch (eventType) {
        case "game_start": {
          const ev = data as GameStartEvent;
          log.push({
            round: 0,
            actor: "system",
            message: `Game started on ${ev.topology_name} (${ev.max_rounds} rounds, budget ${ev.budget})`,
          });
          play.attackerPosition = ev.attacker_entry;
          break;
        }
        case "defender_setup": {
          const ev = data as DefenderSetupEvent;
          play.deployedAssets = ev.deployed_assets;
          log.push({
            round: 0,
            actor: "defender",
            message: `Deployed ${ev.deployed_assets.length} assets (spent ${ev.total_spent.toFixed(1)}, remaining ${ev.remaining_budget.toFixed(1)})`,
          });
          break;
        }
        case "round_start": {
          const ev = data as RoundStartEvent;
          play.currentRound = ev.round;
          play.attackerPosition = ev.attacker_position;
          play.attackerPath = ev.attacker_path;
          play.compromisedNodes = ev.compromised_nodes;
          log.push({
            round: ev.round,
            actor: "system",
            message: `Round ${ev.round} — Attacker at ${ev.attacker_position}`,
          });
          break;
        }
        case "attacker_action": {
          const ev = data as AttackerActionEvent;
          play.attackerPosition = ev.new_position;
          play.compromisedNodes = ev.compromised_nodes;
          play.exfiltratedValue = ev.exfiltrated_value;
          for (const action of ev.actions) {
            log.push({
              round: ev.round,
              actor: "attacker",
              message: `${action.action} on ${action.node_id} (${action.technique_id})`,
            });
          }
          if (ev.actions.length === 0) {
            log.push({
              round: ev.round,
              actor: "attacker",
              message: "No action taken",
            });
          }
          break;
        }
        case "round_result": {
          const ev = data as RoundResultEvent;
          play.detections = [...play.detections, ...ev.detections];
          if (ev.detections.length > 0) {
            for (const det of ev.detections) {
              log.push({
                round: ev.round,
                actor: "system",
                message: `Detection! ${det.asset_type} on ${det.node_id} caught ${det.technique_id}`,
              });
            }
          }
          if (ev.game_over) {
            play.winner = ev.winner;
          }
          break;
        }
        case "game_end": {
          const ev = data as GameEndEvent;
          play.status = "finished";
          play.winner = ev.winner;
          play.attackerPath = ev.attacker_path;
          play.compromisedNodes = ev.compromised_nodes;
          log.push({
            round: ev.rounds_played,
            actor: "system",
            message: `Game over — ${ev.winner} wins! (${ev.rounds_played} rounds, ${ev.total_detections} detections, ${ev.attacker_exfiltrated.toFixed(1)} exfiltrated)`,
          });
          break;
        }
      }

      play.actionLog = log;
      return { play };
    });
  },
}));
