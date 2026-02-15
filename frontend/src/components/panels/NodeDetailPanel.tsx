import { useGameStore } from "../../state/useGameStore";
import MathTooltip from "./MathTooltip";

export default function NodeDetailPanel() {
  const { selectedNodeId, solution, topologyData, setSelectedNode } =
    useGameStore();

  if (!selectedNodeId || !solution || !topologyData) return null;

  const breakdown = solution.node_breakdowns.find(
    (b) => b.node_id === selectedNodeId,
  );
  const nodeInfo = topologyData.nodes.find((n) => n.id === selectedNodeId);
  if (!breakdown || !nodeInfo) return null;

  const p = breakdown.detection_probability;
  const v = breakdown.value;
  const isTarget = solution.attacker_target === selectedNodeId;

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-4 text-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h3 className="font-bold text-gray-100">{selectedNodeId}</h3>
          {isTarget && (
            <span className="text-[10px] bg-yellow-500/20 text-yellow-400 px-1.5 py-0.5 rounded">
              Attacker Target
            </span>
          )}
          {nodeInfo.is_entry_point && (
            <span className="text-[10px] bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded">
              Entry Point
            </span>
          )}
        </div>
        <button
          onClick={() => setSelectedNode(null)}
          className="text-gray-500 hover:text-gray-300 text-xs"
        >
          Close
        </button>
      </div>

      <div className="grid grid-cols-2 gap-x-8 gap-y-2 mb-4">
        <div>
          <span className="text-gray-500 text-xs">Type</span>
          <p className="font-mono text-gray-300">{nodeInfo.node_type}</p>
        </div>
        <div>
          <span className="text-gray-500 text-xs">OS</span>
          <p className="font-mono text-gray-300">{nodeInfo.os}</p>
        </div>
        <div>
          <span className="text-gray-500 text-xs">Value v(t)</span>
          <p className="font-mono text-gray-300">{v.toFixed(1)}</p>
        </div>
        <div>
          <span className="text-gray-500 text-xs">Detection p(t)</span>
          <p className="font-mono text-gray-300">{p.toFixed(4)}</p>
        </div>
      </div>

      {/* Coverage breakdown */}
      {Object.keys(breakdown.coverage).length > 0 && (
        <div className="mb-4">
          <span className="text-gray-500 text-xs block mb-1">
            Coverage allocation
          </span>
          <div className="flex gap-3">
            {Object.entries(breakdown.coverage).map(([asset, prob]) => (
              <div
                key={asset}
                className="bg-gray-800 rounded px-2 py-1 text-xs font-mono"
              >
                {asset}: {prob.toFixed(3)}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Utility formulas */}
      <div className="space-y-2 border-t border-gray-800 pt-3">
        <p className="text-xs text-gray-500 font-medium">Utility Terms</p>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-gray-800/50 rounded p-2">
            <MathTooltip
              latex={`U_d^c(t) = \\alpha \\cdot v(t) = ${breakdown.defender_covered_utility.toFixed(2)}`}
            />
          </div>
          <div className="bg-gray-800/50 rounded p-2">
            <MathTooltip
              latex={`U_d^u(t) = -v(t) = ${breakdown.defender_uncovered_utility.toFixed(2)}`}
            />
          </div>
          <div className="bg-gray-800/50 rounded p-2">
            <MathTooltip
              latex={`U_a^c(t) = -\\beta \\cdot v(t) = ${breakdown.attacker_covered_utility.toFixed(2)}`}
            />
          </div>
          <div className="bg-gray-800/50 rounded p-2">
            <MathTooltip
              latex={`U_a^u(t) = v(t) = ${breakdown.attacker_uncovered_utility.toFixed(2)}`}
            />
          </div>
        </div>

        <div className="space-y-1 pt-2">
          <p className="text-xs text-gray-500 font-medium">Expected Utilities</p>
          <div className="bg-gray-800/50 rounded p-2 text-xs">
            <MathTooltip
              latex={`EU_d(c,t) = p(t) \\cdot U_d^c + (1-p(t)) \\cdot U_d^u = ${breakdown.defender_expected_utility.toFixed(4)}`}
            />
          </div>
          <div className="bg-gray-800/50 rounded p-2 text-xs">
            <MathTooltip
              latex={`EU_a(c,t) = p(t) \\cdot U_a^c + (1-p(t)) \\cdot U_a^u = ${breakdown.attacker_expected_utility.toFixed(4)}`}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
