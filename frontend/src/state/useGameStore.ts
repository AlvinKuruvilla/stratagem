/** Zustand store for global dashboard state. */

import { create } from "zustand";
import { api } from "../api/client";
import type {
  CompareResponse,
  SolutionResponse,
  TopologyResponse,
  TopologyStats,
} from "../api/types";

interface GameState {
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

  // UI
  selectedNodeId: string | null;
  loading: boolean;
  error: string | null;

  // Actions
  init: () => Promise<void>;
  setTopology: (name: string) => Promise<void>;
  setBudget: (budget: number) => void;
  setAlpha: (alpha: number) => void;
  setBeta: (beta: number) => void;
  setShowBaselines: (show: boolean) => void;
  setSelectedNode: (nodeId: string | null) => void;
  fetchSolution: () => Promise<void>;
  fetchComparison: () => Promise<void>;
}

export const useGameStore = create<GameState>((set, get) => ({
  topologies: [],
  selectedTopology: "small",
  topologyData: null,
  budget: 5.0,
  alpha: 1.0,
  beta: 1.0,
  solution: null,
  comparison: null,
  showBaselines: false,
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
}));
