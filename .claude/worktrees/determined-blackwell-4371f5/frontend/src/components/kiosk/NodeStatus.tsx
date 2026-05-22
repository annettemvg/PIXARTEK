"use client";
import { clsx } from "clsx";
import type { NodeStatus as NodeStatusType, NodeState } from "@/types/session";

const STATE_DOT: Record<NodeState, string> = {
  ok:       "bg-emerald-400 shadow-emerald-400/60",
  degraded: "bg-amber-400 shadow-amber-400/60",
  error:    "bg-rose-500 shadow-rose-500/60",
  offline:  "bg-gray-600",
};

const STATE_LABEL: Record<NodeState, string> = {
  ok:       "En línea",
  degraded: "Degradado",
  error:    "Error",
  offline:  "Sin conexión",
};

interface Props {
  nodes: NodeStatusType[];
}

export default function NodeStatus({ nodes }: Props) {
  return (
    <div className="flex flex-col gap-2">
      {nodes.map(node => (
        <div key={node.id} className="flex items-center justify-between px-3 py-2 rounded-lg bg-white/5">
          <div className="flex items-center gap-2">
            <span className={clsx("w-2.5 h-2.5 rounded-full shadow-md shrink-0", STATE_DOT[node.state])} />
            <span className="text-sm">{node.label}</span>
          </div>
          <span className={clsx(
            "text-xs",
            node.state === "ok" ? "text-emerald-400" :
            node.state === "degraded" ? "text-amber-400" :
            node.state === "error" ? "text-rose-400" : "text-gray-500"
          )}>
            {STATE_LABEL[node.state]}
          </span>
        </div>
      ))}
    </div>
  );
}
