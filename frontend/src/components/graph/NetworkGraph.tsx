import {
  ReactFlow,
  Background,
  Controls,
  type NodeTypes,
  type NodeMouseHandler,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useGameStore } from "../../state/useGameStore";
import { useLayoutNodes } from "./useLayoutNodes";
import GraphNode from "./GraphNode";

const nodeTypes: NodeTypes = {
  gameNode: GraphNode,
};

function GraphLegend() {
  return (
    <div className="absolute bottom-3 left-3 z-10 w-[140px] rounded-lg bg-surface-1/80 backdrop-blur-sm border border-border-default text-[10px] text-gray-400 overflow-hidden">
      {/* Detection Probability */}
      <div className="px-2.5 py-2 space-y-1.5">
        <p className="font-semibold text-gray-300 tracking-wide uppercase text-[9px]">
          Detection Prob.
        </p>
        <div className="grid grid-cols-2 gap-1">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-sm bg-gray-700 shrink-0" />
            <span>None</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-sm bg-green-500 shrink-0" />
            <span>Low</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-sm bg-yellow-500 shrink-0" />
            <span>Mid</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-sm bg-red-500 shrink-0" />
            <span>High</span>
          </div>
        </div>
      </div>
      {/* Node Borders */}
      <div className="px-2.5 py-2 border-t border-border-muted space-y-1.5">
        <p className="font-semibold text-gray-300 tracking-wide uppercase text-[9px]">
          Node Borders
        </p>
        <div className="space-y-1">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-sm border-2 border-yellow-400 shrink-0" />
            <span>Target</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-sm border-2 border-dashed border-blue-400 shrink-0" />
            <span>Entry point</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-sm border-2 border-blue-500 shrink-0" />
            <span>Selected</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function NetworkGraph() {
  const { topologyData, solution, selectedNodeId, setSelectedNode } =
    useGameStore();
  const { nodes, edges } = useLayoutNodes(topologyData, solution, selectedNodeId);

  const onNodeClick: NodeMouseHandler = (_, node) => {
    setSelectedNode(node.id === selectedNodeId ? null : node.id);
  };

  return (
    <div className="rounded-xl border border-border-default bg-surface-1 overflow-hidden">
      {/* Section header */}
      <div className="px-5 py-3 border-b border-border-muted">
        <h2 className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase">
          Network Graph
        </h2>
      </div>
      <div className="h-[480px] relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodeClick={onNodeClick}
          fitView
          fitViewOptions={{ padding: 0.15 }}
          minZoom={0.3}
          maxZoom={2}
          proOptions={{ hideAttribution: true }}
          className="bg-surface-0"
        >
          <Background color="#1a1a1f" gap={20} />
          <Controls
            showInteractive={false}
            className="!bg-surface-2 !border-border-default !shadow-lg [&>button]:!bg-surface-2 [&>button]:!border-border-default [&>button]:!text-gray-400 [&>button:hover]:!bg-surface-3"
          />
        </ReactFlow>
        <GraphLegend />
      </div>
    </div>
  );
}
