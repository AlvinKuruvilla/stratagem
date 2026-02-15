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
    <div className="rounded-xl border border-border-default bg-surface-1 overflow-hidden">
      {/* Header */}
      <div className="px-5 py-3 border-b border-border-muted flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-gray-100">{selectedNodeId}</h3>
          {isTarget && (
            <span className="text-[10px] bg-yellow-500/15 text-yellow-400 px-2 py-0.5 rounded-full font-medium">
              Attacker Target
            </span>
          )}
          {nodeInfo.is_entry_point && (
            <span className="text-[10px] bg-blue-500/15 text-blue-400 px-2 py-0.5 rounded-full font-medium">
              Entry Point
            </span>
          )}
        </div>
        <button
          onClick={() => setSelectedNode(null)}
          className="text-gray-500 hover:text-gray-300 text-xs hover:bg-surface-3 px-2 py-1 rounded-md"
        >
          Close
        </button>
      </div>

      {/* Body */}
      <div className="px-5 py-4 text-sm">
        <div className="grid grid-cols-4 gap-4 mb-4">
          <div>
            <span className="text-gray-500 text-[10px] uppercase tracking-wider font-medium">Type</span>
            <p className="font-mono text-gray-300 mt-0.5">{nodeInfo.node_type}</p>
          </div>
          <div>
            <span className="text-gray-500 text-[10px] uppercase tracking-wider font-medium">OS</span>
            <p className="font-mono text-gray-300 mt-0.5">{nodeInfo.os}</p>
          </div>
          <div>
            <span className="text-gray-500 text-[10px] uppercase tracking-wider font-medium">Value v(t)</span>
            <p className="font-mono text-gray-300 mt-0.5">{v.toFixed(1)}</p>
          </div>
          <div>
            <span className="text-gray-500 text-[10px] uppercase tracking-wider font-medium">Detection p(t)</span>
            <p className="font-mono text-gray-300 mt-0.5">{p.toFixed(4)}</p>
          </div>
        </div>

        {/* Coverage breakdown */}
        {Object.keys(breakdown.coverage).length > 0 && (
          <div className="mb-4">
            <span className="text-gray-500 text-[10px] uppercase tracking-wider font-medium block mb-1.5">
              Coverage allocation
            </span>
            <div className="flex flex-wrap gap-2">
              {Object.entries(breakdown.coverage).map(([asset, prob]) => (
                <div
                  key={asset}
                  className="bg-surface-2 rounded-md px-2.5 py-1 text-xs font-mono text-gray-300"
                >
                  {asset}: {prob.toFixed(3)}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Utility formulas */}
        <div className="space-y-2 border-t border-border-muted pt-4">
          <p className="text-[10px] uppercase tracking-wider font-medium text-gray-500">
            Utility Terms
          </p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-surface-2 rounded-lg p-2.5">
              <MathTooltip
                latex={`U_d^c(t) = \\alpha \\cdot v(t) = ${breakdown.defender_covered_utility.toFixed(2)}`}
              />
            </div>
            <div className="bg-surface-2 rounded-lg p-2.5">
              <MathTooltip
                latex={`U_d^u(t) = -v(t) = ${breakdown.defender_uncovered_utility.toFixed(2)}`}
              />
            </div>
            <div className="bg-surface-2 rounded-lg p-2.5">
              <MathTooltip
                latex={`U_a^c(t) = -\\beta \\cdot v(t) = ${breakdown.attacker_covered_utility.toFixed(2)}`}
              />
            </div>
            <div className="bg-surface-2 rounded-lg p-2.5">
              <MathTooltip
                latex={`U_a^u(t) = v(t) = ${breakdown.attacker_uncovered_utility.toFixed(2)}`}
              />
            </div>
          </div>

          <div className="space-y-1 pt-2">
            <p className="text-[10px] uppercase tracking-wider font-medium text-gray-500">
              Expected Utilities
            </p>
            <div className="bg-surface-2 rounded-lg p-2.5 text-xs">
              <MathTooltip
                latex={`EU_d(c,t) = p(t) \\cdot U_d^c + (1-p(t)) \\cdot U_d^u = ${breakdown.defender_expected_utility.toFixed(4)}`}
              />
            </div>
            <div className="bg-surface-2 rounded-lg p-2.5 text-xs">
              <MathTooltip
                latex={`EU_a(c,t) = p(t) \\cdot U_a^c + (1-p(t)) \\cdot U_a^u = ${breakdown.attacker_expected_utility.toFixed(4)}`}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
