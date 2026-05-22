"use client";
import { useState, useRef, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { adjustProjection, setProjectionAngle, type ProjectionAction } from "@/lib/api-client";
import PixartekLogo from "@/components/ui/PixartekLogo";
import { clsx } from "clsx";

const KEY_MAP: Record<string, ProjectionAction> = {
  ArrowUp:    "up",
  ArrowDown:  "down",
  ArrowLeft:  "left",
  ArrowRight: "right",
  "+":        "zoom_in",
  "=":        "zoom_in",
  "-":        "zoom_out",
  "[":        "rotate_left",
  "]":        "rotate_right",
  "r":        "reset",
  "R":        "reset",
};

/* ── Btn is OUTSIDE the page component so React never remounts it on re-render ── */
function Btn({
  onClick,
  label,
  color = "ink",
  size = "md",
}: {
  onClick: () => void;
  label: string;
  color?: "ink" | "coral" | "teal";
  size?: "md" | "lg";
}) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        "flex items-center justify-center rounded-2xl font-display font-800 select-none",
        "active:scale-95 transition-transform duration-75 shadow-btn touch-none",
        size === "lg" ? "w-24 h-24 text-3xl" : "w-20 h-20 text-2xl",
        color === "coral" && "bg-pixartek-coral text-white",
        color === "ink"   && "bg-pixartek-ink text-white",
        color === "teal"  && "bg-teal-500 text-white",
      )}
    >
      {label}
    </button>
  );
}

export default function ProjectionPage() {
  const router = useRouter();
  const [feedback, setFeedback] = useState("");
  const busyRef = useRef(false);
  const [angle, setAngle] = useState(0);
  const angleTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Safety: reset busyRef after 4 s max so a timeout never locks the UI
  const busyResetTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const send = useCallback(async (action: ProjectionAction) => {
    if (busyRef.current) return;
    busyRef.current = true;

    // Safety timeout — ensure busyRef is never stuck forever
    if (busyResetTimer.current) clearTimeout(busyResetTimer.current);
    busyResetTimer.current = setTimeout(() => { busyRef.current = false; }, 4000);

    try {
      await adjustProjection(action);
      setFeedback(action);
      setTimeout(() => setFeedback(""), 500);
    } catch {
      setFeedback("error");
    } finally {
      busyRef.current = false;
      if (busyResetTimer.current) clearTimeout(busyResetTimer.current);
    }
  }, []);

  // Slider rotation — debounced so it only fires when you stop dragging
  function handleAngleChange(val: number) {
    setAngle(val);
    if (angleTimer.current) clearTimeout(angleTimer.current);
    angleTimer.current = setTimeout(async () => {
      try {
        await setProjectionAngle(val);
        setFeedback(`${val}°`);
        setTimeout(() => setFeedback(""), 800);
      } catch { setFeedback("error"); }
    }, 80);
  }

  // Keyboard shortcuts
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      const action = KEY_MAP[e.key];
      if (!action) return;
      e.preventDefault();
      send(action);
    };
    window.addEventListener("keydown", down);
    return () => window.removeEventListener("keydown", down);
  }, [send]);

  return (
    <div className="flex flex-col h-screen bg-pixartek-cream overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 bg-white border-b border-pixartek-border shrink-0">
        <div className="flex items-center gap-4">
          <button onClick={() => router.push("/settings")} className="hover:opacity-70 transition">
            <PixartekLogo size="sm" />
          </button>
          <div className="h-6 w-px bg-pixartek-border" />
          <h1 className="font-display font-700 text-lg text-pixartek-ink">Ajuste de Proyección</h1>
        </div>
        <div className={clsx(
          "px-3 py-1 rounded-full text-xs font-body font-600 transition-all",
          feedback === "error" ? "bg-rose-100 text-rose-600" :
          feedback ? "bg-emerald-100 text-emerald-700" : "bg-pixartek-cream text-pixartek-muted"
        )}>
          {feedback === "error" ? "⚠ sin conexión" : feedback ? `✓ ${feedback}` : "listo"}
        </div>
      </header>

      <div className="flex-1 flex flex-col items-center justify-center gap-8 px-6 py-4">

        {/* Row 1: Zoom */}
        <div className="flex flex-col items-center gap-2">
          <span className="text-xs font-body text-pixartek-muted uppercase tracking-widest">Zoom</span>
          <div className="flex gap-4">
            <Btn onClick={() => send("zoom_out")} label="−" color="coral" size="lg" />
            <Btn onClick={() => send("zoom_in")}  label="+" color="coral" size="lg" />
          </div>
        </div>

        {/* Row 2: D-pad */}
        <div className="flex flex-col items-center gap-0">
          <span className="text-xs font-body text-pixartek-muted uppercase tracking-widest mb-2">Posición</span>
          <Btn onClick={() => send("up")} label="▲" />
          <div className="flex gap-0">
            <Btn onClick={() => send("left")}  label="◀" />
            <div className="w-20 h-20 bg-white border-2 border-pixartek-border flex items-center justify-center rounded-none">
              <span className="text-pixartek-muted text-lg">✛</span>
            </div>
            <Btn onClick={() => send("right")} label="▶" />
          </div>
          <Btn onClick={() => send("down")} label="▼" />
        </div>

        {/* Row 3: Rotation slider */}
        <div className="flex flex-col items-center gap-3 w-full max-w-sm">
          <div className="flex items-center justify-between w-full">
            <span className="text-xs font-body text-pixartek-muted uppercase tracking-widest">Rotación</span>
            <span className="text-sm font-display font-700 text-pixartek-ink w-14 text-right">{angle}°</span>
          </div>
          <input
            type="range"
            min={-45}
            max={45}
            step={0.5}
            value={angle}
            onChange={e => handleAngleChange(Number(e.target.value))}
            className="w-full h-3 rounded-full accent-teal-500 cursor-pointer"
          />
          <div className="flex justify-between w-full text-xs text-pixartek-muted font-body">
            <span>−45°</span>
            <button
              onClick={() => handleAngleChange(0)}
              className="text-pixartek-coral font-600 hover:underline"
            >
              centrar
            </button>
            <span>+45°</span>
          </div>
        </div>

        {/* Reset */}
        <button
          onClick={() => { setAngle(0); send("reset"); }}
          className="px-8 py-3 rounded-2xl border-2 border-pixartek-border font-body font-600 text-pixartek-muted hover:border-pixartek-ink/40 hover:text-pixartek-ink transition"
        >
          ↺ Restablecer todo
        </button>

        {/* Keyboard legend */}
        <div className="bg-white border border-pixartek-border rounded-2xl px-5 py-3 text-xs font-body text-pixartek-muted grid grid-cols-2 gap-x-6 gap-y-1">
          <span><kbd className="bg-pixartek-cream px-1.5 py-0.5 rounded border border-pixartek-border font-mono">← → ↑ ↓</kbd> mover</span>
          <span><kbd className="bg-pixartek-cream px-1.5 py-0.5 rounded border border-pixartek-border font-mono">+ -</kbd> zoom</span>
          <span>🖱 arrastra el slider para rotar</span>
          <span><kbd className="bg-pixartek-cream px-1.5 py-0.5 rounded border border-pixartek-border font-mono">R</kbd> reset</span>
        </div>
      </div>
    </div>
  );
}
