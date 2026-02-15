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
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
      <h3 className="text-sm font-medium text-gray-400 mb-3">
        Defender Expected Utility: SSE vs Baselines
      </h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ left: 20, right: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="name"
            tick={{ fill: "#9ca3af", fontSize: 11 }}
          />
          <YAxis tick={{ fill: "#9ca3af", fontSize: 10 }} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "1px solid #374151",
              borderRadius: "6px",
              fontSize: "12px",
            }}
          />
          <Bar dataKey="eu" name="Defender EU">
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
  );
}
