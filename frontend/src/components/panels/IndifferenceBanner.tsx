import { useGameStore } from "../../state/useGameStore";

export default function IndifferenceBanner() {
  const { solution } = useGameStore();
  if (!solution) return null;

  // Find nodes whose attacker EU is within tolerance of the equilibrium value
  const eqEU = solution.attacker_expected_utility;
  const tol = 0.01;
  const equalizedNodes = solution.node_breakdowns
    .filter((b) => Math.abs(b.attacker_expected_utility - eqEU) < tol)
    .map((b) => b.node_id);

  return (
    <div className="rounded-xl border border-blue-500/20 bg-blue-500/5 px-5 py-3 flex items-start gap-3">
      <div className="mt-0.5 shrink-0 w-5 h-5 rounded-full bg-blue-500/20 flex items-center justify-center">
        <svg className="w-3 h-3 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <div className="text-sm">
        <span className="text-blue-400 font-medium">Indifference Principle:</span>{" "}
        <span className="text-gray-300">
          Top {equalizedNodes.length} target{equalizedNodes.length !== 1 ? "s" : ""}{" "}
          equalized at EU<sub>a</sub> ={" "}
          <span className="font-mono">{eqEU.toFixed(4)}</span>
        </span>
        <span className="text-gray-500 ml-2 font-mono text-xs">
          [{equalizedNodes.join(", ")}]
        </span>
      </div>
    </div>
  );
}
