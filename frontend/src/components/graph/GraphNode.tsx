import { Handle, Position } from "@xyflow/react";

interface GraphNodeData {
  label: string;
  nodeType: string;
  value: number;
  isEntryPoint: boolean;
  isTarget: boolean;
  detectionProb: number;
  [key: string]: unknown;
}

const TYPE_ICONS: Record<string, string> = {
  firewall: "FW",
  router: "RT",
  server: "SV",
  workstation: "WS",
  database: "DB",
};

export default function GraphNode({ data }: { data: GraphNodeData }) {
  const icon = TYPE_ICONS[data.nodeType] ?? "??";

  return (
    <>
      <Handle type="target" position={Position.Top} className="!opacity-0 !w-2 !h-2" />
      <div className="flex flex-col items-center gap-0.5 select-none">
        <div className="flex items-center gap-1">
          <span className="text-[9px] font-bold text-gray-400 bg-black/30 px-1 py-px rounded text-center leading-none">
            {icon}
          </span>
          <span className="font-medium truncate max-w-[90px]">{data.label}</span>
          {data.isTarget && <span className="text-yellow-400 text-[10px]">&#9733;</span>}
        </div>
        <div className="text-[9px] text-gray-300/80 font-mono flex gap-2">
          <span>v={data.value.toFixed(1)}</span>
          <span>p={data.detectionProb.toFixed(2)}</span>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!opacity-0 !w-2 !h-2" />
    </>
  );
}
