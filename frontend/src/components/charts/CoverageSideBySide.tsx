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
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
      <h3 className="text-sm font-medium text-gray-400 mb-3">
        Per-Node Detection Probability: SSE vs Baselines
      </h3>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} margin={{ left: 20, right: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="node"
            tick={{ fill: "#9ca3af", fontSize: 9 }}
            angle={-45}
            textAnchor="end"
            height={60}
          />
          <YAxis
            tick={{ fill: "#9ca3af", fontSize: 10 }}
            domain={[0, 1]}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "1px solid #374151",
              borderRadius: "6px",
              fontSize: "12px",
            }}
          />
          <Legend
            wrapperStyle={{ fontSize: "11px", color: "#9ca3af" }}
          />
          <Bar dataKey="SSE" fill="#3b82f6" />
          <Bar dataKey="Uniform" fill="#a855f7" />
          <Bar dataKey="Static" fill="#f97316" />
          <Bar dataKey="Heuristic" fill="#14b8a6" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
