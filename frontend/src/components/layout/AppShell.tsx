import type { ReactNode } from "react";
import ControlPanel from "./ControlPanel";

export default function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <ControlPanel />
      <main className="flex-1 overflow-y-auto p-4 space-y-4">{children}</main>
    </div>
  );
}
