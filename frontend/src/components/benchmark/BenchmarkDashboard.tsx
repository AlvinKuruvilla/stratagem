import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { useGameStore } from "../../state/useGameStore";
import type {
  BenchmarkMetricSummary,
  StrategyMetricsResponse,
} from "../../api/types";

const STRATEGY_COLORS: Record<string, string> = {
  sse_optimal: "#3b82f6",
  uniform: "#a855f7",
  static: "#f97316",
  heuristic: "#14b8a6",
};

const STRATEGY_LABELS: Record<string, string> = {
  sse_optimal: "SSE",
  uniform: "Uniform",
  static: "Static",
  heuristic: "Heuristic",
};

const tooltipStyle = {
  backgroundColor: "#111113",
  border: "1px solid #27272a",
  borderRadius: "8px",
  fontSize: "12px",
  fontFamily: "'JetBrains Mono', monospace",
  boxShadow: "0 4px 12px rgba(0,0,0,0.4)",
};

function fmt(m: BenchmarkMetricSummary, pct = false): string {
  if (m.n === 0 || m.mean < 0) return "N/A";
  if (pct) return `${(m.mean * 100).toFixed(1)}%`;
  return m.mean.toFixed(3);
}

function fmtFull(m: BenchmarkMetricSummary, pct = false): string {
  if (m.n === 0 || m.mean < 0) return "N/A";
  if (pct)
    return `${(m.mean * 100).toFixed(1)}% \u00b1 ${(m.std * 100).toFixed(1)}%`;
  return `${m.mean.toFixed(3)} \u00b1 ${m.std.toFixed(3)}`;
}

// ── Detection Rate Chart ─────────────────────────────────────────────

function DetectionRateChart({
  metrics,
}: {
  metrics: StrategyMetricsResponse[];
}) {
  // Group by topology, with one bar per strategy.
  const topologies = [...new Set(metrics.map((m) => m.topology))];
  const strategies = [...new Set(metrics.map((m) => m.strategy))];

  const data = topologies.map((topo) => {
    const row: Record<string, string | number> = { topology: topo };
    for (const strategy of strategies) {
      const m = metrics.find(
        (x) => x.topology === topo && x.strategy === strategy
      );
      row[strategy] = m ? m.detection_rate.mean * 100 : 0;
    }
    return row;
  });

  return (
    <div className="rounded-xl border border-border-default bg-surface-1 overflow-hidden">
      <div className="px-5 py-3 border-b border-border-muted">
        <h3 className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase">
          Detection Rate by Strategy
        </h3>
        <p className="text-xs text-gray-600 mt-0.5">
          Percentage of trials where the attacker was detected
        </p>
      </div>
      <div className="px-5 py-4">
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data} margin={{ left: 10, right: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e1e22" />
            <XAxis
              dataKey="topology"
              tick={{ fill: "#71717a", fontSize: 11 }}
            />
            <YAxis
              tick={{ fill: "#71717a", fontSize: 10 }}
              domain={[0, 100]}
              tickFormatter={(v: number) => `${v}%`}
            />
            <Tooltip
              contentStyle={tooltipStyle}
              formatter={(value: number) => `${value.toFixed(1)}%`}
            />
            <Legend
              formatter={(value: string) => STRATEGY_LABELS[value] ?? value}
              wrapperStyle={{ fontSize: "11px" }}
            />
            {strategies.map((strategy) => (
              <Bar
                key={strategy}
                dataKey={strategy}
                name={strategy}
                fill={STRATEGY_COLORS[strategy] ?? "#6b7280"}
                radius={[4, 4, 0, 0]}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ── Metrics Table ────────────────────────────────────────────────────

function MetricsTable({ metrics }: { metrics: StrategyMetricsResponse[] }) {
  return (
    <div className="rounded-xl border border-border-default bg-surface-1 overflow-hidden">
      <div className="px-5 py-3 border-b border-border-muted">
        <h3 className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase">
          Detailed Metrics
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-border-muted">
              <th className="px-4 py-2 text-left text-gray-500 font-medium">
                Strategy
              </th>
              <th className="px-4 py-2 text-left text-gray-500 font-medium">
                Topology
              </th>
              <th className="px-4 py-2 text-right text-gray-500 font-medium">
                Det. Rate
              </th>
              <th className="px-4 py-2 text-right text-gray-500 font-medium">
                MTTD
              </th>
              <th className="px-4 py-2 text-right text-gray-500 font-medium">
                Cost Eff.
              </th>
              <th className="px-4 py-2 text-right text-gray-500 font-medium">
                Dwell
              </th>
              <th className="px-4 py-2 text-right text-gray-500 font-medium">
                Utility
              </th>
              <th className="px-4 py-2 text-right text-gray-500 font-medium">
                Exfil
              </th>
            </tr>
          </thead>
          <tbody>
            {metrics.map((m) => {
              const isSSE = m.strategy === "sse_optimal";
              const rowClass = isSSE
                ? "bg-blue-500/5 border-b border-border-muted"
                : "border-b border-border-muted";
              return (
                <tr key={`${m.strategy}-${m.topology}`} className={rowClass}>
                  <td
                    className={`px-4 py-2 font-mono ${isSSE ? "text-blue-400 font-semibold" : "text-gray-300"}`}
                  >
                    {STRATEGY_LABELS[m.strategy] ?? m.strategy}
                  </td>
                  <td className="px-4 py-2 text-gray-400">{m.topology}</td>
                  <td className="px-4 py-2 text-right text-gray-300 font-mono">
                    {fmtFull(m.detection_rate, true)}
                  </td>
                  <td className="px-4 py-2 text-right text-gray-300 font-mono">
                    {fmtFull(m.mean_time_to_detect)}
                  </td>
                  <td className="px-4 py-2 text-right text-gray-300 font-mono">
                    {fmtFull(m.cost_efficiency)}
                  </td>
                  <td className="px-4 py-2 text-right text-gray-300 font-mono">
                    {fmtFull(m.attacker_dwell_time)}
                  </td>
                  <td className="px-4 py-2 text-right text-gray-300 font-mono">
                    {fmtFull(m.defender_utility)}
                  </td>
                  <td className="px-4 py-2 text-right text-gray-300 font-mono">
                    {fmtFull(m.attacker_exfiltration)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Significance Badges ──────────────────────────────────────────────

function SignificanceTable() {
  const { benchmark } = useGameStore();
  const comparisons = benchmark.result?.comparisons ?? [];

  if (comparisons.length === 0) return null;

  return (
    <div className="rounded-xl border border-border-default bg-surface-1 overflow-hidden">
      <div className="px-5 py-3 border-b border-border-muted">
        <h3 className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase">
          Statistical Significance
        </h3>
        <p className="text-xs text-gray-600 mt-0.5">
          Mann-Whitney U test (p &lt; 0.05)
        </p>
      </div>
      <div className="px-5 py-3 flex flex-wrap gap-2">
        {comparisons.map((c, i) => (
          <div
            key={i}
            className={`inline-flex items-center gap-1.5 text-[10px] font-medium px-2.5 py-1 rounded-full border ${
              c.significant
                ? "bg-green-500/10 border-green-500/30 text-green-400"
                : "bg-gray-500/10 border-gray-500/20 text-gray-500"
            }`}
          >
            <span>
              SSE vs {STRATEGY_LABELS[c.strategy_b] ?? c.strategy_b}
            </span>
            <span className="opacity-60">({c.metric})</span>
            <span className="font-mono">p={c.p_value.toFixed(3)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main Dashboard ───────────────────────────────────────────────────

export default function BenchmarkDashboard() {
  const { benchmark } = useGameStore();

  if (benchmark.status === "idle" && !benchmark.result) {
    return (
      <div className="flex items-center justify-center h-64 text-sm text-gray-500">
        Configure benchmark parameters and click "Run Benchmark" to start.
      </div>
    );
  }

  if (benchmark.status === "running") {
    return (
      <div className="flex items-center justify-center h-64 gap-3 text-sm text-gray-400">
        <div className="h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        Running benchmark...
      </div>
    );
  }

  const result = benchmark.result;
  if (!result) return null;

  return (
    <div className="space-y-6">
      <DetectionRateChart metrics={result.strategy_metrics} />

      <MetricsTable metrics={result.strategy_metrics} />

      <SignificanceTable />

      <div className="text-xs text-gray-600">
        {result.num_trials} total trials across {result.topologies.length}{" "}
        topologies and {result.strategies.length} strategies
      </div>
    </div>
  );
}
