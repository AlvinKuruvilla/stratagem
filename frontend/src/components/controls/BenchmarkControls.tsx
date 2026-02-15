import { useGameStore } from "../../state/useGameStore";

const TOPOLOGY_OPTIONS = ["small", "medium", "large"];

export default function BenchmarkControls() {
  const {
    benchmark,
    setBenchmarkTrials,
    setBenchmarkBudget,
    setBenchmarkMaxRounds,
    setBenchmarkTopologies,
    runBenchmark,
  } = useGameStore();

  const isRunning = benchmark.status === "running";

  const toggleTopology = (topo: string) => {
    const current = benchmark.topologies;
    if (current.includes(topo)) {
      if (current.length > 1) {
        setBenchmarkTopologies(current.filter((t) => t !== topo));
      }
    } else {
      setBenchmarkTopologies([...current, topo]);
    }
  };

  return (
    <div className="space-y-3">
      {/* Trials */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="text-xs font-medium text-gray-400">Trials</label>
          <span className="text-[11px] font-mono bg-surface-2 text-gray-300 px-1.5 py-0.5 rounded">
            {benchmark.trials}
          </span>
        </div>
        <input
          type="range"
          min={10}
          max={500}
          step={10}
          value={benchmark.trials}
          onChange={(e) => setBenchmarkTrials(parseInt(e.target.value))}
          disabled={isRunning}
          className="w-full"
        />
        <div className="flex justify-between text-[10px] text-gray-500 mt-0.5">
          <span>10</span>
          <span>500</span>
        </div>
      </div>

      {/* Budget */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="text-xs font-medium text-gray-400">Budget</label>
          <span className="text-[11px] font-mono bg-surface-2 text-gray-300 px-1.5 py-0.5 rounded">
            {benchmark.budget.toFixed(1)}
          </span>
        </div>
        <input
          type="range"
          min={1}
          max={30}
          step={0.5}
          value={benchmark.budget}
          onChange={(e) => setBenchmarkBudget(parseFloat(e.target.value))}
          disabled={isRunning}
          className="w-full"
        />
        <div className="flex justify-between text-[10px] text-gray-500 mt-0.5">
          <span>1</span>
          <span>30</span>
        </div>
      </div>

      {/* Max Rounds */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="text-xs font-medium text-gray-400">Max Rounds</label>
          <span className="text-[11px] font-mono bg-surface-2 text-gray-300 px-1.5 py-0.5 rounded">
            {benchmark.maxRounds}
          </span>
        </div>
        <input
          type="range"
          min={1}
          max={20}
          step={1}
          value={benchmark.maxRounds}
          onChange={(e) => setBenchmarkMaxRounds(parseInt(e.target.value))}
          disabled={isRunning}
          className="w-full"
        />
        <div className="flex justify-between text-[10px] text-gray-500 mt-0.5">
          <span>1</span>
          <span>20</span>
        </div>
      </div>

      {/* Topologies */}
      <div>
        <label className="text-xs font-medium text-gray-400 block mb-1.5">
          Topologies
        </label>
        <div className="flex gap-1.5">
          {TOPOLOGY_OPTIONS.map((topo) => (
            <button
              key={topo}
              onClick={() => toggleTopology(topo)}
              disabled={isRunning}
              className={`flex-1 text-[10px] font-medium py-1 rounded-md border transition-colors ${
                benchmark.topologies.includes(topo)
                  ? "bg-blue-600/20 border-blue-500/40 text-blue-400"
                  : "bg-surface-2 border-border-default text-gray-500 hover:text-gray-400"
              }`}
            >
              {topo}
            </button>
          ))}
        </div>
      </div>

      {/* Run */}
      <button
        onClick={runBenchmark}
        disabled={isRunning}
        className={`w-full text-xs font-semibold py-2 rounded-lg transition-colors ${
          isRunning
            ? "bg-gray-700 text-gray-400 cursor-not-allowed"
            : "bg-blue-600 hover:bg-blue-700 text-white"
        }`}
      >
        {isRunning ? "Running..." : "Run Benchmark"}
      </button>
    </div>
  );
}
