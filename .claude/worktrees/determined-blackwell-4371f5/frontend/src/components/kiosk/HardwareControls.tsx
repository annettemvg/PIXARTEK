"use client";
import { clsx } from "clsx";

interface Props {
  dispensing: boolean;
  cleaning: boolean;
  onDispense: () => void;
  onClean: () => void;
}

export default function HardwareControls({ dispensing, cleaning, onDispense, onClean }: Props) {
  return (
    <div className="flex gap-3">
      <button
        onClick={onDispense}
        disabled={dispensing || cleaning}
        className={clsx(
          "flex-1 flex flex-col items-center gap-1.5 py-3 rounded-xl border text-sm font-semibold transition active:scale-95",
          dispensing
            ? "border-amber-400 bg-amber-400/20 text-amber-300 animate-pulse"
            : "border-white/20 hover:border-amber-400/60 hover:bg-amber-400/10 text-gray-300 hover:text-amber-300 disabled:opacity-40 disabled:cursor-not-allowed"
        )}
      >
        <span className="text-xl">🎨</span>
        <span>{dispensing ? "Dispensando..." : "Pigmento"}</span>
      </button>

      <button
        onClick={onClean}
        disabled={dispensing || cleaning}
        className={clsx(
          "flex-1 flex flex-col items-center gap-1.5 py-3 rounded-xl border text-sm font-semibold transition active:scale-95",
          cleaning
            ? "border-blue-400 bg-blue-400/20 text-blue-300 animate-pulse"
            : "border-white/20 hover:border-blue-400/60 hover:bg-blue-400/10 text-gray-300 hover:text-blue-300 disabled:opacity-40 disabled:cursor-not-allowed"
        )}
      >
        <span className="text-xl">🚿</span>
        <span>{cleaning ? "Limpiando..." : "Limpiar pincel"}</span>
      </button>
    </div>
  );
}
