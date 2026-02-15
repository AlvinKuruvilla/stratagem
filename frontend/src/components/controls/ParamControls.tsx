import { useEffect, useRef } from "react";
import { useGameStore } from "../../state/useGameStore";

export default function ParamControls() {
  const {
    alpha,
    beta,
    setAlpha,
    setBeta,
    fetchSolution,
    fetchComparison,
    showBaselines,
  } = useGameStore();
  const timerRef = useRef<ReturnType<typeof setTimeout>>(null);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(async () => {
      await fetchSolution();
      if (showBaselines) await fetchComparison();
    }, 500);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [alpha, beta, fetchSolution, fetchComparison, showBaselines]);

  return (
    <div className="space-y-3">
      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="text-xs font-medium text-gray-400">
            Alpha <span className="text-gray-600">(defender reward)</span>
          </label>
          <span className="text-[11px] font-mono bg-surface-2 text-gray-300 px-1.5 py-0.5 rounded">
            {alpha.toFixed(1)}
          </span>
        </div>
        <input
          type="range"
          min={0.1}
          max={3.0}
          step={0.1}
          value={alpha}
          onChange={(e) => setAlpha(parseFloat(e.target.value))}
          className="w-full"
        />
      </div>
      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="text-xs font-medium text-gray-400">
            Beta <span className="text-gray-600">(attacker penalty)</span>
          </label>
          <span className="text-[11px] font-mono bg-surface-2 text-gray-300 px-1.5 py-0.5 rounded">
            {beta.toFixed(1)}
          </span>
        </div>
        <input
          type="range"
          min={0.1}
          max={3.0}
          step={0.1}
          value={beta}
          onChange={(e) => setBeta(parseFloat(e.target.value))}
          className="w-full"
        />
      </div>
    </div>
  );
}
