import TopologySelector from "../controls/TopologySelector";
import BudgetSlider from "../controls/BudgetSlider";
import ParamControls from "../controls/ParamControls";
import BaselineToggle from "../controls/BaselineToggle";
import ModeToggle from "../controls/ModeToggle";
import PlayControls from "../controls/PlayControls";
import { useGameStore } from "../../state/useGameStore";

function SectionLabel({ children }: { children: string }) {
  return (
    <p className="text-[10px] font-semibold tracking-widest text-gray-500 uppercase">
      {children}
    </p>
  );
}

export default function ControlPanel() {
  const { mode, solution, play } = useGameStore();

  return (
    <aside className="w-64 shrink-0 bg-surface-1 border-r border-border-default flex flex-col overflow-y-auto">
      {/* Brand */}
      <div className="px-5 py-4 border-b border-border-muted">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-blue-600 flex items-center justify-center text-[10px] font-bold text-white">
            S
          </div>
          <div>
            <h1 className="text-sm font-semibold text-gray-100 tracking-tight">
              Stratagem
            </h1>
            <p className="text-[10px] text-gray-500 -mt-0.5">
              Security Game Dashboard
            </p>
          </div>
        </div>
      </div>

      {/* Mode Toggle */}
      <div className="px-5 py-3 border-b border-border-muted">
        <ModeToggle />
      </div>

      {/* Controls */}
      <div className="flex-1 px-5 py-4 space-y-5">
        <div className="space-y-2">
          <SectionLabel>Network</SectionLabel>
          <TopologySelector />
        </div>

        {mode === "solver" ? (
          <>
            <div className="space-y-2">
              <SectionLabel>Parameters</SectionLabel>
              <BudgetSlider />
              <ParamControls />
            </div>

            <div className="space-y-2">
              <SectionLabel>Strategy</SectionLabel>
              <BaselineToggle />
            </div>
          </>
        ) : (
          <div className="space-y-2">
            <SectionLabel>Game Setup</SectionLabel>
            <PlayControls />
          </div>
        )}
      </div>

      {/* Footer */}
      {mode === "solver" && solution && (
        <div className="mt-auto border-t border-border-default px-5 py-4 text-xs space-y-1.5">
          <SectionLabel>SSE Result</SectionLabel>
          <p className="text-gray-400">
            Target:{" "}
            <span className="text-yellow-400 font-mono font-medium">
              {solution.attacker_target}
            </span>
          </p>
          <p className="text-gray-400">
            Defender EU:{" "}
            <span className="text-green-400 font-mono font-medium">
              {solution.defender_expected_utility.toFixed(4)}
            </span>
          </p>
          <p className="text-gray-400">
            Attacker EU:{" "}
            <span className="text-red-400 font-mono font-medium">
              {solution.attacker_expected_utility.toFixed(4)}
            </span>
          </p>
        </div>
      )}

      {mode === "play" && play.status !== "idle" && (
        <div className="mt-auto border-t border-border-default px-5 py-4 text-xs space-y-1.5">
          <SectionLabel>Game Status</SectionLabel>
          <p className="text-gray-400">
            Round:{" "}
            <span className="text-blue-400 font-mono font-medium">
              {play.currentRound}
            </span>
          </p>
          <p className="text-gray-400">
            Exfiltrated:{" "}
            <span className="text-red-400 font-mono font-medium">
              {play.exfiltratedValue.toFixed(1)}
            </span>
          </p>
          {play.winner && (
            <p className="text-gray-400">
              Winner:{" "}
              <span
                className={`font-mono font-medium ${
                  play.winner === "defender" ? "text-green-400" : "text-red-400"
                }`}
              >
                {play.winner}
              </span>
            </p>
          )}
        </div>
      )}
    </aside>
  );
}
