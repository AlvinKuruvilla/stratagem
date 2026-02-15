/** Typed fetch wrappers for the Stratagem API. */

import type {
  CompareResponse,
  SolveRequest,
  SolutionResponse,
  TopologyResponse,
  TopologyStats,
} from "./types";

const BASE = "/api";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path}: ${res.status}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path}: ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  listTopologies: () => get<TopologyStats[]>("/topologies"),
  getTopology: (name: string) => get<TopologyResponse>(`/topologies/${name}`),
  solve: (req: SolveRequest) => post<SolutionResponse>("/solve", req),
  compare: (req: SolveRequest) => post<CompareResponse>("/compare", req),
};
