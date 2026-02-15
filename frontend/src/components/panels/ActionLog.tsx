import { useEffect, useRef } from "react";
import { useGameStore } from "../../state/useGameStore";

const ACTOR_STYLE: Record<string, { bg: string; text: string; label: string }> = {
  attacker: { bg: "bg-red-500/20", text: "text-red-400", label: "ATK" },
  defender: { bg: "bg-blue-500/20", text: "text-blue-400", label: "DEF" },
  system: { bg: "bg-yellow-500/20", text: "text-yellow-400", label: "SYS" },
};

export default function ActionLog() {
  const { play } = useGameStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [play.actionLog.length]);

  if (play.actionLog.length === 0) return null;

  return (
    <div className="rounded-xl border border-border-default bg-surface-1 overflow-hidden">
      <div className="px-5 py-3 border-b border-border-muted">
        <h2 className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase">
          Action Log
        </h2>
      </div>
      <div ref={scrollRef} className="max-h-[240px] overflow-y-auto px-4 py-3 space-y-1.5">
        {play.actionLog.map((entry, i) => {
          const style = ACTOR_STYLE[entry.actor] ?? ACTOR_STYLE.system;
          return (
            <div key={i} className="flex items-start gap-2 text-[11px]">
              <span
                className={`shrink-0 px-1.5 py-0.5 rounded font-bold ${style.bg} ${style.text}`}
              >
                {style.label}
              </span>
              {entry.round > 0 && (
                <span className="text-gray-500 font-mono shrink-0">R{entry.round}</span>
              )}
              <span className="text-gray-300">{entry.message}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
