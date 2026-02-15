import { Handle, Position } from "@xyflow/react";
import type { DeployedAsset } from "../../api/types";

interface GraphNodeData {
  label: string;
  nodeType: string;
  value: number;
  isEntryPoint: boolean;
  isTarget: boolean;
  detectionProb: number;
  isAttackerHere?: boolean;
  isCompromised?: boolean;
  deployedAssets?: DeployedAsset[];
  [key: string]: unknown;
}

const TYPE_ICONS: Record<string, string> = {
  firewall: "FW",
  router: "RT",
  server: "SV",
  workstation: "WS",
  database: "DB",
};

const ASSET_COLORS: Record<string, string> = {
  honeypot: "bg-purple-500",
  decoy_credential: "bg-cyan-500",
  honeytoken: "bg-amber-500",
};

export default function GraphNode({ data }: { data: GraphNodeData }) {
  const icon = TYPE_ICONS[data.nodeType] ?? "??";
  const assets = data.deployedAssets ?? [];

  return (
    <>
      <Handle type="target" position={Position.Top} className="!opacity-0 !w-2 !h-2" />
      <div className="flex flex-col items-center gap-0.5 select-none">
        <div className="flex items-center gap-1">
          {data.isAttackerHere && (
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 attacker-pulse shrink-0" />
          )}
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
        {assets.length > 0 && (
          <div className="flex gap-1 mt-0.5">
            {assets.map((a, i) => (
              <span
                key={i}
                className={`w-1.5 h-1.5 rounded-full ${ASSET_COLORS[a.asset_type] ?? "bg-gray-500"}`}
                title={`${a.asset_type} (det=${a.detection_probability})`}
              />
            ))}
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Bottom} className="!opacity-0 !w-2 !h-2" />
    </>
  );
}
