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

// ── Play mode types ──────────────────────────────────

export interface PlayGameRequest {
  topology: string;
  budget: number;
  max_rounds: number;
  seed: number;
  defender_strategy: string;
}

export interface DeployedAsset {
  asset_type: string;
  node_id: string;
  detection_probability: number;
  cost: number;
}

export interface AttackerAction {
  action: string;
  node_id: string;
  technique_id: string;
  success: boolean;
  value: number;
}

export interface Detection {
  node_id: string;
  asset_type: string;
  technique_id: string;
}

export interface ActionLogEntry {
  round: number;
  actor: "attacker" | "defender" | "system";
  message: string;
}

export interface GameStartEvent {
  topology_name: string;
  max_rounds: number;
  budget: number;
  attacker_entry: string;
  seed: number;
}

export interface DefenderSetupEvent {
  deployed_assets: DeployedAsset[];
  total_spent: number;
  remaining_budget: number;
}

export interface RoundStartEvent {
  round: number;
  attacker_position: string;
  compromised_nodes: string[];
  attacker_path: string[];
}

export interface AttackerActionEvent {
  round: number;
  actions: AttackerAction[];
  new_position: string;
  compromised_nodes: string[];
  exfiltrated_value: number;
}

export interface RoundResultEvent {
  round: number;
  detections: Detection[];
  attacker_detected: boolean;
  game_over: boolean;
  winner: string;
}

export interface GameEndEvent {
  winner: string;
  rounds_played: number;
  total_detections: number;
  attacker_exfiltrated: number;
  attacker_path: string[];
  compromised_nodes: string[];
}
