"use client";
import { clsx } from "clsx";
import { useState, useEffect } from "react";
import type { VisionFeedback } from "@/types/session";

interface Props { feedback: VisionFeedback | null; }

function PrecisionRing({ value }: { value: number }) {
  const r = 28;
  const circ = 2 * Math.PI * r;
  const offset = circ - (value / 100) * circ;
  const color = value >= 85 ? "#7DC4A8" : value >= 65 ? "#D4B85A" : "#E07B6A";
  return (
    <div className="relative flex items-center justify-center w-20 h-20">
      <svg className="absolute -rotate-90" width="80" height="80">
        <circle cx="40" cy="40" r={r} fill="none" stroke="#E8E4DE" strokeWidth="6" />
        <circle cx="40" cy="40" r={r} fill="none" stroke={color} strokeWidth="6"
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.8s ease" }} />
      </svg>
      <span className="font-display font-800 text-xl" style={{ color }}>{value}%</span>
    </div>
  );
}

function CameraViewer() {
  const [frameIndex, setFrameIndex] = useState(0);

  useEffect(() => {
    // Update frame index every 333ms to force re-fetch
    // This creates a continuous live feed without caching
    const interval = setInterval(() => {
      setFrameIndex(i => i + 1);
    }, 333);

    return () => clearInterval(interval);
  }, []);

  // Add timestamp to URL to bypass cache
  const timestamp = Date.now();
  const frameUrl = `/api/vision/camera-frame?t=${timestamp}&frame=${frameIndex}`;

  return (
    <div className="w-full bg-black rounded-xl overflow-hidden border-2 border-pixartek-border">
      {/* Live feed indicator */}
      <div className="relative bg-black aspect-video flex items-center justify-center group">
        <img
          key={`frame-${frameIndex}`}
          src={frameUrl}
          alt="Live camera feed - RPi4 Vision (244)"
          className="w-full h-full object-cover"
          onError={(e) => {
            const img = e.target as HTMLImageElement;
            img.style.display = "none";
          }}
        />

        {/* Live indicator badge */}
        <div className="absolute top-2 left-2 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-600 text-white text-xs font-display font-700 shadow-lg">
          <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
          LIVE
        </div>

        {/* Camera info */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent px-3 py-2">
          <p className="font-body text-xs text-white/80">📷 RPi4-A (244) - Visión</p>
        </div>
      </div>
    </div>
  );
}

export default function FeedbackPanel({ feedback }: Props) {
  if (!feedback) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-8 text-pixartek-muted">
        <span className="text-3xl animate-pulse">👁</span>
        <p className="font-body text-xs text-center text-pixartek-muted">Esperando análisis de visión…</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-4">
        <PrecisionRing value={feedback.precision_pct} />
        <div className="flex flex-col gap-1">
          <p className="font-body text-xs text-pixartek-muted">Precisión de trazo</p>
          <p className="font-body text-xs text-pixartek-muted mt-2">Desv. de color</p>
          <p className={clsx("font-display font-700 text-sm",
            feedback.color_deviation < 3 ? "text-pixartek-mint" :
            feedback.color_deviation < 7 ? "text-pixartek-yellow" : "text-pixartek-coral")}>
            ΔE {feedback.color_deviation.toFixed(1)}
          </p>
        </div>
      </div>

      {feedback.stroke_errors.length > 0 && (
        <div className="flex flex-col gap-1.5">
          <p className="font-display font-600 text-xs text-pixartek-muted uppercase tracking-widest">Errores</p>
          {feedback.stroke_errors.map((e, i) => (
            <div key={i} className="flex items-start gap-2 bg-rose-50 border border-rose-200 rounded-xl px-3 py-2">
              <span className="text-rose-400 text-xs mt-0.5 shrink-0">⚠</span>
              <div>
                <p className="font-body text-xs font-700 text-rose-600">{e.zone}</p>
                <p className="font-body text-xs text-pixartek-muted">{e.message}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {feedback.suggestions.length > 0 && (
        <div className="flex flex-col gap-1.5">
          <p className="font-display font-600 text-xs text-pixartek-muted uppercase tracking-widest">Sugerencias</p>
          {feedback.suggestions.map((s, i) => (
            <div key={i} className="flex items-start gap-2 bg-sky-50 border border-sky-200 rounded-xl px-3 py-2">
              <span className="text-pixartek-sky text-xs mt-0.5 shrink-0">→</span>
              <p className="font-body text-xs text-pixartek-muted">{s}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
