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

const tooltipStyle = {
  backgroundColor: "#111113",
  border: "1px solid #27272a",
  borderRadius: "8px",
  fontSize: "12px",
  fontFamily: "'JetBrains Mono', monospace",
  boxShadow: "0 4px 12px rgba(0,0,0,0.4)",
};

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
    <div className="rounded-xl border border-border-default bg-surface-1 overflow-hidden">
      <div className="px-5 py-3 border-b border-border-muted">
        <h3 className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase">
          Attacker Expected Utility
        </h3>
        <p className="text-xs text-gray-600 mt-0.5">Per node — indifference principle</p>
      </div>
      <div className="px-5 py-4">
        <ResponsiveContainer width="100%" height={Math.max(200, data.length * 28)}>
          <BarChart data={data} layout="vertical" margin={{ left: 60, right: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e1e22" />
            <XAxis type="number" tick={{ fill: "#71717a", fontSize: 10 }} />
            <YAxis
              type="category"
              dataKey="node"
              tick={{ fill: "#71717a", fontSize: 10 }}
              width={55}
            />
            <Tooltip contentStyle={tooltipStyle} />
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
            <Bar dataKey="eu" name="EU_a" radius={[0, 3, 3, 0]}>
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
    </div>
  );
}
