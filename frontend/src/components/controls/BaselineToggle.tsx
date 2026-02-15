import { useGameStore } from "../../state/useGameStore";

export default function BaselineToggle() {
  const { showBaselines, setShowBaselines } = useGameStore();

  return (
    <label className="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        checked={showBaselines}
        onChange={(e) => setShowBaselines(e.target.checked)}
        className="accent-blue-500"
      />
      <span className="text-xs text-gray-400">
        Compare with baselines
      </span>
    </label>
  );
}
