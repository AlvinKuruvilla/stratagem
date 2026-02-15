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
    <div className="space-y-2">
      <div>
        <label className="block text-xs font-medium text-gray-400 mb-1">
          Alpha (defender reward): {alpha.toFixed(1)}
        </label>
        <input
          type="range"
          min={0.1}
          max={3.0}
          step={0.1}
          value={alpha}
          onChange={(e) => setAlpha(parseFloat(e.target.value))}
          className="w-full accent-blue-500"
        />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-400 mb-1">
          Beta (attacker penalty): {beta.toFixed(1)}
        </label>
        <input
          type="range"
          min={0.1}
          max={3.0}
          step={0.1}
          value={beta}
          onChange={(e) => setBeta(parseFloat(e.target.value))}
          className="w-full accent-blue-500"
        />
      </div>
    </div>
  );
}
