import { useGameStore } from "../../state/useGameStore";

const MODES = [
  { value: "solver" as const, label: "Solver" },
  { value: "play" as const, label: "Play" },
  { value: "benchmark" as const, label: "Bench" },
];

export default function ModeToggle() {
  const { mode, setMode } = useGameStore();

  return (
    <div className="flex rounded-lg bg-surface-2 p-0.5">
      {MODES.map((m) => (
        <button
          key={m.value}
          onClick={() => setMode(m.value)}
          className={`flex-1 text-xs font-medium py-1.5 rounded-md transition-colors ${
            mode === m.value
              ? "bg-blue-600 text-white"
              : "text-gray-400 hover:text-gray-300"
          }`}
        >
          {m.label}
        </button>
      ))}
    </div>
  );
}
