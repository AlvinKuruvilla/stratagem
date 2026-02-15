/** Dagre layout for React Flow nodes. */

import { useMemo } from "react";
import dagre from "dagre";
import type { Node, Edge } from "@xyflow/react";
import type { TopologyResponse } from "../../api/types";
import type { SolutionResponse } from "../../api/types";

const NODE_WIDTH = 140;
const NODE_HEIGHT = 50;

/** Interpolate between green → yellow → red based on detection probability. */
function coverageColor(p: number): string {
  if (p <= 0) return "#374151"; // gray-700 (no coverage)
  if (p < 0.3) return "#22c55e"; // green
  if (p < 0.6) return "#eab308"; // yellow
  return "#ef4444"; // red
}

export function useLayoutNodes(
  topology: TopologyResponse | null,
  solution: SolutionResponse | null,
  selectedNodeId: string | null,
) {
  return useMemo(() => {
    if (!topology) return { nodes: [] as Node[], edges: [] as Edge[] };

    const g = new dagre.graphlib.Graph();
    g.setDefaultEdgeLabel(() => ({}));
    g.setGraph({ rankdir: "TB", nodesep: 60, ranksep: 80 });

    // Build a lookup from solution
    const breakdownMap = new Map(
      solution?.node_breakdowns.map((b) => [b.node_id, b]) ?? [],
    );

    for (const node of topology.nodes) {
      g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
    }

    for (const edge of topology.edges) {
      g.setEdge(edge.source, edge.target);
    }

    dagre.layout(g);

    const nodes: Node[] = topology.nodes.map((node) => {
      const pos = g.node(node.id);
      const breakdown = breakdownMap.get(node.id);
      const p = breakdown?.detection_probability ?? 0;
      const isTarget = solution?.attacker_target === node.id;
      const isSelected = selectedNodeId === node.id;

      return {
        id: node.id,
        position: {
          x: pos.x - NODE_WIDTH / 2,
          y: pos.y - NODE_HEIGHT / 2,
        },
        data: {
          label: node.id,
          nodeType: node.node_type,
          value: node.value,
          isEntryPoint: node.is_entry_point,
          isTarget,
          detectionProb: p,
        },
        type: "gameNode",
        style: {
          width: NODE_WIDTH,
          height: NODE_HEIGHT,
          background: coverageColor(p),
          border: isTarget
            ? "2px solid #facc15"
            : node.is_entry_point
              ? "2px dashed #60a5fa"
              : isSelected
                ? "2px solid #3b82f6"
                : "1px solid #4b5563",
          borderRadius: "6px",
          color: "#f9fafb",
          fontSize: "11px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column" as const,
          padding: "4px",
          opacity: 1,
          cursor: "pointer",
        },
      };
    });

    const edges: Edge[] = topology.edges.map((edge, i) => ({
      id: `e-${i}`,
      source: edge.source,
      target: edge.target,
      type: "default",
    }));

    return { nodes, edges };
  }, [topology, solution, selectedNodeId]);
}
