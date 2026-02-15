import { useGameStore } from "../../state/useGameStore";

export default function TopologySelector() {
  const { topologies, selectedTopology, setTopology } = useGameStore();

  return (
    <div>
      <label className="block text-xs font-medium text-gray-400 mb-1">
        Topology
      </label>
      <select
        value={selectedTopology}
        onChange={(e) => setTopology(e.target.value)}
        className="w-full rounded-md bg-gray-800 border border-gray-700 px-3 py-1.5 text-sm text-gray-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
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
