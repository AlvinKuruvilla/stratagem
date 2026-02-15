import { useGameStore } from "../../state/useGameStore";

export default function BaselineToggle() {
  const { showBaselines, setShowBaselines } = useGameStore();

  return (
    <label className="flex items-center gap-2.5 cursor-pointer group">
      <input
        type="checkbox"
        checked={showBaselines}
        onChange={(e) => setShowBaselines(e.target.checked)}
      />
      <span className="text-xs text-gray-400 group-hover:text-gray-300">
        Compare with baselines
      </span>
    </label>
  );
}
