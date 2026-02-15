import { useEffect, useRef } from "react";
import { useGameStore } from "../../state/useGameStore";

export default function BudgetSlider() {
  const { budget, setBudget, fetchSolution, fetchComparison, showBaselines } =
    useGameStore();
  const timerRef = useRef<ReturnType<typeof setTimeout>>(null);

  // Debounced re-solve on budget change
  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(async () => {
      await fetchSolution();
      if (showBaselines) await fetchComparison();
    }, 300);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [budget, fetchSolution, fetchComparison, showBaselines]);

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <label className="text-xs font-medium text-gray-400">Budget</label>
        <span className="text-[11px] font-mono bg-surface-2 text-gray-300 px-1.5 py-0.5 rounded">
          {budget.toFixed(1)}
        </span>
      </div>
      <input
        type="range"
        min={0}
        max={30}
        step={0.5}
        value={budget}
        onChange={(e) => setBudget(parseFloat(e.target.value))}
        className="w-full"
      />
      <div className="flex justify-between text-[10px] text-gray-500 mt-0.5">
        <span>0</span>
        <span>30</span>
      </div>
    </div>
  );
}
