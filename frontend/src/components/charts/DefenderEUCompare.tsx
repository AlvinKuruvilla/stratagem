import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { useGameStore } from "../../state/useGameStore";

const STRATEGY_COLORS: Record<string, string> = {
  SSE: "#3b82f6",
  Uniform: "#a855f7",
  Static: "#f97316",
  Heuristic: "#14b8a6",
};

const tooltipStyle = {
  backgroundColor: "#111113",
  border: "1px solid #27272a",
  borderRadius: "8px",
  fontSize: "12px",
  fontFamily: "'JetBrains Mono', monospace",
  boxShadow: "0 4px 12px rgba(0,0,0,0.4)",
};

export default function DefenderEUCompare() {
  const { comparison, showBaselines } = useGameStore();
  if (!showBaselines || !comparison) return null;

  const data = [
    { name: "SSE", eu: comparison.sse.defender_expected_utility },
    { name: "Uniform", eu: comparison.uniform.defender_expected_utility },
    { name: "Static", eu: comparison.static.defender_expected_utility },
    { name: "Heuristic", eu: comparison.heuristic.defender_expected_utility },
  ];

  return (
    <div className="rounded-xl border border-border-default bg-surface-1 overflow-hidden">
      <div className="px-5 py-3 border-b border-border-muted">
        <h3 className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase">
          Defender Expected Utility
        </h3>
        <p className="text-xs text-gray-600 mt-0.5">SSE vs baseline strategies</p>
      </div>
      <div className="px-5 py-4">
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={data} margin={{ left: 20, right: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e1e22" />
            <XAxis
              dataKey="name"
              tick={{ fill: "#71717a", fontSize: 11 }}
            />
            <YAxis tick={{ fill: "#71717a", fontSize: 10 }} />
            <Tooltip contentStyle={tooltipStyle} />
            <Bar dataKey="eu" name="Defender EU" radius={[4, 4, 0, 0]}>
              {data.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={STRATEGY_COLORS[entry.name] ?? "#6b7280"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
