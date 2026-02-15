import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { useGameStore } from "../../state/useGameStore";

const tooltipStyle = {
  backgroundColor: "#111113",
  border: "1px solid #27272a",
  borderRadius: "8px",
  fontSize: "12px",
  fontFamily: "'JetBrains Mono', monospace",
  boxShadow: "0 4px 12px rgba(0,0,0,0.4)",
};

export default function CoverageSideBySide() {
  const { comparison, showBaselines } = useGameStore();
  if (!showBaselines || !comparison) return null;

  // Build per-node coverage comparison
  const nodeIds = comparison.sse.node_breakdowns.map((b) => b.node_id);
  const uniformMap = new Map(
    comparison.uniform.node_breakdowns.map((b) => [b.node_id, b]),
  );
  const staticMap = new Map(
    comparison.static.node_breakdowns.map((b) => [b.node_id, b]),
  );
  const heuristicMap = new Map(
    comparison.heuristic.node_breakdowns.map((b) => [b.node_id, b]),
  );

  const data = nodeIds.map((nid) => {
    const sse = comparison.sse.node_breakdowns.find((b) => b.node_id === nid);
    return {
      node: nid,
      SSE: parseFloat((sse?.detection_probability ?? 0).toFixed(3)),
      Uniform: parseFloat(
        (uniformMap.get(nid)?.detection_probability ?? 0).toFixed(3),
      ),
      Static: parseFloat(
        (staticMap.get(nid)?.detection_probability ?? 0).toFixed(3),
      ),
      Heuristic: parseFloat(
        (heuristicMap.get(nid)?.detection_probability ?? 0).toFixed(3),
      ),
    };
  });

  return (
    <div className="rounded-xl border border-border-default bg-surface-1 overflow-hidden">
      <div className="px-5 py-3 border-b border-border-muted">
        <h3 className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase">
          Per-Node Detection Probability
        </h3>
        <p className="text-xs text-gray-600 mt-0.5">SSE vs baseline strategies</p>
      </div>
      <div className="px-5 py-4">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={data} margin={{ left: 20, right: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e1e22" />
            <XAxis
              dataKey="node"
              tick={{ fill: "#71717a", fontSize: 9 }}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis
              tick={{ fill: "#71717a", fontSize: 10 }}
              domain={[0, 1]}
            />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend
              wrapperStyle={{ fontSize: "11px", color: "#71717a" }}
            />
            <Bar dataKey="SSE" fill="#3b82f6" radius={[3, 3, 0, 0]} />
            <Bar dataKey="Uniform" fill="#a855f7" radius={[3, 3, 0, 0]} />
            <Bar dataKey="Static" fill="#f97316" radius={[3, 3, 0, 0]} />
            <Bar dataKey="Heuristic" fill="#14b8a6" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
