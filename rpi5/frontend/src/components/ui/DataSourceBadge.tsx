import { clsx } from "clsx";
import type { DataSource } from "@/hooks/useArtworks";

export default function DataSourceBadge({ source }: { source: DataSource }) {
  return (
    <span className={clsx(
      "flex items-center gap-1.5 text-xs px-2 py-1 rounded-full border",
      source === "api"
        ? "border-emerald-500/40 text-emerald-400 bg-emerald-500/10"
        : "border-amber-500/40 text-amber-400 bg-amber-500/10"
    )}>
      <span className={clsx("w-1.5 h-1.5 rounded-full", source === "api" ? "bg-emerald-400" : "bg-amber-400")} />
      {source === "api" ? "Backend API" : "Demo (mock)"}
    </span>
  );
}
