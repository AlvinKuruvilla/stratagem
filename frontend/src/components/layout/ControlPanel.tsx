import TopologySelector from "../controls/TopologySelector";
import BudgetSlider from "../controls/BudgetSlider";
import ParamControls from "../controls/ParamControls";
import BaselineToggle from "../controls/BaselineToggle";
import { useGameStore } from "../../state/useGameStore";

export default function ControlPanel() {
  const { solution } = useGameStore();

  return (
    <aside className="w-64 shrink-0 bg-gray-900 border-r border-gray-800 p-4 flex flex-col gap-5 overflow-y-auto">
      <div>
        <h1 className="text-lg font-bold text-blue-400 tracking-tight">
          Stratagem
        </h1>
        <p className="text-[10px] text-gray-500 mt-0.5">
          Stackelberg Security Game Dashboard
        </p>
      </div>

      <TopologySelector />
      <BudgetSlider />
      <ParamControls />

      <div className="border-t border-gray-800 pt-3">
        <BaselineToggle />
      </div>

      {solution && (
        <div className="border-t border-gray-800 pt-3 text-xs space-y-1">
          <p className="text-gray-400 font-medium">SSE Result</p>
          <p>
            Target:{" "}
            <span className="text-yellow-400 font-mono">
              {solution.attacker_target}
            </span>
          </p>
          <p>
            Defender EU:{" "}
            <span className="text-green-400 font-mono">
              {solution.defender_expected_utility.toFixed(4)}
            </span>
          </p>
          <p>
            Attacker EU:{" "}
            <span className="text-red-400 font-mono">
              {solution.attacker_expected_utility.toFixed(4)}
            </span>
          </p>
        </div>
      )}
    </aside>
  );
}
