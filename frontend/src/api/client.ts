/** Typed fetch wrappers for the Stratagem API. */

import type {
  CompareResponse,
  PlayGameRequest,
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

export function streamGame(
  req: PlayGameRequest,
  onEvent: (eventType: string, data: unknown) => void,
  onError: (err: Error) => void,
): AbortController {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${BASE}/play`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req),
        signal: controller.signal,
      });

      if (!res.ok) {
        onError(new Error(`POST /play: ${res.status}`));
        return;
      }

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";

        for (const part of parts) {
          if (!part.trim()) continue;
          let eventType = "message";
          let dataStr = "";
          for (const line of part.split("\n")) {
            if (line.startsWith("event: ")) {
              eventType = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
              dataStr = line.slice(6);
            }
          }
          if (dataStr) {
            try {
              onEvent(eventType, JSON.parse(dataStr));
            } catch {
              // skip malformed JSON
            }
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        onError(err as Error);
      }
    }
  })();

  return controller;
}

export const api = {
  listTopologies: () => get<TopologyStats[]>("/topologies"),
  getTopology: (name: string) => get<TopologyResponse>(`/topologies/${name}`),
  solve: (req: SolveRequest) => post<SolutionResponse>("/solve", req),
  compare: (req: SolveRequest) => post<CompareResponse>("/compare", req),
};
