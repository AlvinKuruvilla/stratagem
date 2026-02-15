import { useEffect } from "react";
import { useGameStore } from "./state/useGameStore";
import AppShell from "./components/layout/AppShell";
import IndifferenceBanner from "./components/panels/IndifferenceBanner";
import NetworkGraph from "./components/graph/NetworkGraph";
import NodeDetailPanel from "./components/panels/NodeDetailPanel";
import AttackerEUChart from "./components/charts/AttackerEUChart";
import DefenderEUCompare from "./components/charts/DefenderEUCompare";
import CoverageSideBySide from "./components/charts/CoverageSideBySide";
import GameResultBanner from "./components/panels/GameResultBanner";
import ActionLog from "./components/panels/ActionLog";
import BenchmarkDashboard from "./components/benchmark/BenchmarkDashboard";

export default function App() {
  const { init, loading, error, mode, showBaselines } = useGameStore();

  useEffect(() => {
    init();
  }, [init]);

  return (
    <AppShell>
      {loading && (
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <div className="h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          Loading...
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 px-5 py-3 flex items-start gap-3">
          <div className="mt-0.5 shrink-0 w-5 h-5 rounded-full bg-red-500/20 flex items-center justify-center">
            <svg className="w-3 h-3 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <p className="text-sm text-red-400">
            <span className="font-medium">Error:</span> {error}
          </p>
        </div>
      )}

      {mode === "solver" ? (
        <>
          <IndifferenceBanner />
          <NetworkGraph />
          <NodeDetailPanel />
          <AttackerEUChart />

          {showBaselines && (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <DefenderEUCompare />
              <CoverageSideBySide />
            </div>
          )}
        </>
      ) : mode === "play" ? (
        <>
          <GameResultBanner />
          <NetworkGraph />
          <ActionLog />
        </>
      ) : (
        <BenchmarkDashboard />
      )}
    </AppShell>
  );
}
