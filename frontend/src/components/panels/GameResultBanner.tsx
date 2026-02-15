import { useGameStore } from "../../state/useGameStore";

export default function GameResultBanner() {
  const { play } = useGameStore();

  if (play.status !== "finished") return null;

  const isDefenderWin = play.winner === "defender";

  return (
    <div
      className={`rounded-xl border px-5 py-4 ${
        isDefenderWin
          ? "border-green-500/30 bg-green-500/5"
          : "border-red-500/30 bg-red-500/5"
      }`}
    >
      <div className="flex items-center justify-between">
        <div>
          <h3
            className={`text-sm font-semibold ${
              isDefenderWin ? "text-green-400" : "text-red-400"
            }`}
          >
            {isDefenderWin ? "Defender Wins" : "Attacker Wins"}
          </h3>
          <p className="text-xs text-gray-400 mt-0.5">
            {play.currentRound} rounds played
          </p>
        </div>
        <div className="flex gap-6 text-xs">
          <div className="text-center">
            <p className="text-gray-500">Detections</p>
            <p className="text-gray-200 font-mono font-medium">
              {play.detections.length}
            </p>
          </div>
          <div className="text-center">
            <p className="text-gray-500">Exfiltrated</p>
            <p className="text-gray-200 font-mono font-medium">
              {play.exfiltratedValue.toFixed(1)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-gray-500">Compromised</p>
            <p className="text-gray-200 font-mono font-medium">
              {play.compromisedNodes.length}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
