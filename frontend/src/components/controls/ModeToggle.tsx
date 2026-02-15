import { useGameStore } from "../../state/useGameStore";

export default function ModeToggle() {
  const { mode, setMode } = useGameStore();

  return (
    <div className="flex rounded-lg bg-surface-2 p-0.5">
      <button
        onClick={() => setMode("solver")}
        className={`flex-1 text-xs font-medium py-1.5 rounded-md transition-colors ${
          mode === "solver"
            ? "bg-blue-600 text-white"
            : "text-gray-400 hover:text-gray-300"
        }`}
      >
        Solver
      </button>
      <button
        onClick={() => setMode("play")}
        className={`flex-1 text-xs font-medium py-1.5 rounded-md transition-colors ${
          mode === "play"
            ? "bg-blue-600 text-white"
            : "text-gray-400 hover:text-gray-300"
        }`}
      >
        Play
      </button>
    </div>
  );
}
