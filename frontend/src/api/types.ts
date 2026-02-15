/** TypeScript interfaces mirroring the Pydantic schemas. */

export interface NodeInfo {
  id: string;
  node_type: string;
  os: string;
  services: string[];
  value: number;
  is_entry_point: boolean;
}

export interface EdgeInfo {
  source: string;
  target: string;
  segment: string;
}

export interface TopologyStats {
  name: string;
  node_count: number;
  edge_count: number;
  entry_points: number;
  high_value_targets: number;
}

export interface TopologyResponse {
  name: string;
  nodes: NodeInfo[];
  edges: EdgeInfo[];
}

export interface NodeUtilityBreakdown {
  node_id: string;
  value: number;
  detection_probability: number;
  coverage: Record<string, number>;
  is_entry_point: boolean;
  defender_covered_utility: number;
  defender_uncovered_utility: number;
  attacker_covered_utility: number;
  attacker_uncovered_utility: number;
  defender_expected_utility: number;
  attacker_expected_utility: number;
}

export interface SolutionResponse {
  topology_name: string;
  budget: number;
  alpha: number;
  beta: number;
  attacker_target: string;
  defender_expected_utility: number;
  attacker_expected_utility: number;
  node_breakdowns: NodeUtilityBreakdown[];
}

export interface CompareResponse {
  sse: SolutionResponse;
  uniform: SolutionResponse;
  static: SolutionResponse;
  heuristic: SolutionResponse;
}

export interface SolveRequest {
  topology: string;
  budget: number;
  alpha: number;
  beta: number;
}
