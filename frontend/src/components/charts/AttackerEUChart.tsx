import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { useGameStore } from "../../state/useGameStore";

export default function AttackerEUChart() {
  const { solution } = useGameStore();
  if (!solution) return null;

  const data = [...solution.node_breakdowns]
    .sort((a, b) => b.attacker_expected_utility - a.attacker_expected_utility)
    .map((b) => ({
      node: b.node_id,
      eu: parseFloat(b.attacker_expected_utility.toFixed(4)),
      isTarget: b.node_id === solution.attacker_target,
    }));

  const eqLine = solution.attacker_expected_utility;

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
      <h3 className="text-sm font-medium text-gray-400 mb-3">
        Attacker Expected Utility per Node (Indifference Principle)
      </h3>
      <ResponsiveContainer width="100%" height={Math.max(200, data.length * 28)}>
        <BarChart data={data} layout="vertical" margin={{ left: 60, right: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis type="number" tick={{ fill: "#9ca3af", fontSize: 10 }} />
          <YAxis
            type="category"
            dataKey="node"
            tick={{ fill: "#9ca3af", fontSize: 10 }}
            width={55}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "1px solid #374151",
              borderRadius: "6px",
              fontSize: "12px",
            }}
          />
          <ReferenceLine
            x={eqLine}
            stroke="#facc15"
            strokeDasharray="4 4"
            label={{
              value: `EQ: ${eqLine.toFixed(3)}`,
              fill: "#facc15",
              fontSize: 10,
              position: "top",
            }}
          />
          <Bar dataKey="eu" name="EU_a">
            {data.map((entry, i) => (
              <Cell
                key={i}
                fill={entry.isTarget ? "#facc15" : "#3b82f6"}
                opacity={entry.isTarget ? 1 : 0.7}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
