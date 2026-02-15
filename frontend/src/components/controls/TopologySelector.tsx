import { useGameStore } from "../../state/useGameStore";

export default function TopologySelector() {
  const { topologies, selectedTopology, setTopology } = useGameStore();

  return (
    <div>
      <select
        value={selectedTopology}
        onChange={(e) => setTopology(e.target.value)}
        className="w-full rounded-lg bg-surface-2 border border-border-default px-3 py-1.5 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/50 hover:border-gray-600"
      >
        {topologies.map((t) => (
          <option key={t.name} value={t.name}>
            {t.name} ({t.node_count} nodes, {t.edge_count} edges)
          </option>
        ))}
      </select>
    </div>
  );
}
