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

export default function NetworkGraph() {
  const { topologyData, solution, selectedNodeId, setSelectedNode } =
    useGameStore();
  const { nodes, edges } = useLayoutNodes(topologyData, solution, selectedNodeId);

  const onNodeClick: NodeMouseHandler = (_, node) => {
    setSelectedNode(node.id === selectedNodeId ? null : node.id);
  };

  return (
    <div className="h-[420px] rounded-lg border border-gray-800 bg-gray-900/50 overflow-hidden">
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
        className="bg-gray-950"
      >
        <Background color="#1f2937" gap={20} />
        <Controls
          showInteractive={false}
          className="!bg-gray-800 !border-gray-700 !shadow-lg [&>button]:!bg-gray-800 [&>button]:!border-gray-700 [&>button]:!text-gray-300 [&>button:hover]:!bg-gray-700"
        />
      </ReactFlow>
    </div>
  );
}
