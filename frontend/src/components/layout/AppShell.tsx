import type { ReactNode } from "react";
import ControlPanel from "./ControlPanel";

export default function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-surface-0">
      <ControlPanel />
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-[1400px] mx-auto px-6 py-6 space-y-6">
          {children}
        </div>
      </main>
    </div>
  );
}
