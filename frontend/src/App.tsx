import { useEffect } from "react";
import { useGameStore } from "./state/useGameStore";
import AppShell from "./components/layout/AppShell";
import IndifferenceBanner from "./components/panels/IndifferenceBanner";
import NetworkGraph from "./components/graph/NetworkGraph";
import NodeDetailPanel from "./components/panels/NodeDetailPanel";
import AttackerEUChart from "./components/charts/AttackerEUChart";
import DefenderEUCompare from "./components/charts/DefenderEUCompare";
import CoverageSideBySide from "./components/charts/CoverageSideBySide";

export default function App() {
  const { init, loading, error } = useGameStore();

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
        <div className="rounded-md bg-red-950/50 border border-red-800/50 px-4 py-2 text-sm text-red-400">
          Error: {error}
        </div>
      )}

      <IndifferenceBanner />
      <NetworkGraph />
      <NodeDetailPanel />
      <AttackerEUChart />
      <DefenderEUCompare />
      <CoverageSideBySide />
    </AppShell>
  );
}
