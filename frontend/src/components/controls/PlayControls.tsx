import { useGameStore } from "../../state/useGameStore";

const STRATEGIES = [
  { value: "sse_optimal", label: "SSE Optimal" },
  { value: "uniform", label: "Uniform Random" },
  { value: "static", label: "Protect High-Value" },
  { value: "heuristic", label: "Cover Chokepoints" },
];

export default function PlayControls() {
  const {
    play,
    setPlayBudget,
    setPlayMaxRounds,
    setPlaySeed,
    setPlayDefenderStrategy,
    startGame,
    stopGame,
  } = useGameStore();

  const isRunning = play.status === "running";

  return (
    <div className="space-y-3">
      {/* Budget */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="text-xs font-medium text-gray-400">Budget</label>
          <span className="text-[11px] font-mono bg-surface-2 text-gray-300 px-1.5 py-0.5 rounded">
            {play.budget.toFixed(1)}
          </span>
        </div>
        <input
          type="range"
          min={0}
          max={30}
          step={0.5}
          value={play.budget}
          onChange={(e) => setPlayBudget(parseFloat(e.target.value))}
          disabled={isRunning}
          className="w-full"
        />
        <div className="flex justify-between text-[10px] text-gray-500 mt-0.5">
          <span>0</span>
          <span>30</span>
        </div>
      </div>

      {/* Max Rounds */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="text-xs font-medium text-gray-400">Max Rounds</label>
          <span className="text-[11px] font-mono bg-surface-2 text-gray-300 px-1.5 py-0.5 rounded">
            {play.maxRounds}
          </span>
        </div>
        <input
          type="range"
          min={1}
          max={20}
          step={1}
          value={play.maxRounds}
          onChange={(e) => setPlayMaxRounds(parseInt(e.target.value))}
          disabled={isRunning}
          className="w-full"
        />
        <div className="flex justify-between text-[10px] text-gray-500 mt-0.5">
          <span>1</span>
          <span>20</span>
        </div>
      </div>

      {/* Seed */}
      <div>
        <label className="text-xs font-medium text-gray-400 block mb-1">Seed</label>
        <input
          type="number"
          value={play.seed}
          onChange={(e) => setPlaySeed(parseInt(e.target.value) || 0)}
          disabled={isRunning}
          className="w-full text-xs bg-surface-2 border border-border-default rounded-md px-2.5 py-1.5 text-gray-300 font-mono focus:border-blue-500 focus:outline-none"
        />
      </div>

      {/* Defender Strategy */}
      <div>
        <label className="text-xs font-medium text-gray-400 block mb-1">
          Defender Strategy
        </label>
        <select
          value={play.defenderStrategy}
          onChange={(e) => setPlayDefenderStrategy(e.target.value)}
          disabled={isRunning}
          className="w-full text-xs bg-surface-2 border border-border-default rounded-md px-2.5 py-1.5 text-gray-300 focus:border-blue-500 focus:outline-none"
        >
          {STRATEGIES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      </div>

      {/* Start / Stop */}
      <button
        onClick={isRunning ? stopGame : startGame}
        className={`w-full text-xs font-semibold py-2 rounded-lg transition-colors ${
          isRunning
            ? "bg-red-600 hover:bg-red-700 text-white"
            : "bg-blue-600 hover:bg-blue-700 text-white"
        }`}
      >
        {isRunning ? "Stop Game" : "Start Game"}
      </button>
    </div>
  );
}
