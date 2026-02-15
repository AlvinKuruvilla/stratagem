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
    <div className="rounded-md bg-blue-950/50 border border-blue-800/50 px-4 py-2 text-sm">
      <span className="text-blue-400 font-medium">Indifference Principle:</span>{" "}
      <span className="text-gray-300">
        Top {equalizedNodes.length} target{equalizedNodes.length !== 1 ? "s" : ""}{" "}
        equalized at EU<sub>a</sub> = {eqEU.toFixed(4)}
      </span>
      <span className="text-gray-500 ml-2">
        [{equalizedNodes.join(", ")}]
      </span>
    </div>
  );
}
