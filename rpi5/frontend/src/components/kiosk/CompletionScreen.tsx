"use client";
import { useMemo } from "react";
import { useRouter } from "next/navigation";
import type { StageMetric } from "@/types/session";
import type { Artwork } from "@/types/artwork";
import PixartekLogo from "@/components/ui/PixartekLogo";

interface Props {
  artwork: Artwork;
  stageMetrics: StageMetric[];
  elapsed_s: number;
  profileName?: string;
}

function formatTime(s: number) {
  const m = Math.floor(s / 60).toString().padStart(2, "0");
  const sec = (s % 60).toString().padStart(2, "0");
  return `${m}:${sec}`;
}

function getAchievement(avg: number) {
  if (avg >= 90) return { emoji: "🏆", label: "Maestro",    color: "#D4B85A" };
  if (avg >= 75) return { emoji: "🎨", label: "Artista",    color: "#E07B6A" };
  if (avg >= 60) return { emoji: "🖌️", label: "Aprendiz",   color: "#7096BC" };
  return              { emoji: "🌱", label: "Explorador", color: "#7DC4A8" };
}

export default function CompletionScreen({ artwork, stageMetrics, elapsed_s, profileName }: Props) {
  const router = useRouter();

  const avgPrecision = useMemo(() => {
    if (!stageMetrics.length) return 0;
    return Math.round(stageMetrics.reduce((acc, m) => acc + m.precision_pct, 0) / stageMetrics.length);
  }, [stageMetrics]);

  const avgDeviation = useMemo(() => {
    if (!stageMetrics.length) return 0;
    return (stageMetrics.reduce((acc, m) => acc + m.color_deviation, 0) / stageMetrics.length).toFixed(1);
  }, [stageMetrics]);

  const achievement = getAchievement(avgPrecision);

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-pixartek-cream px-6 text-center relative overflow-hidden">

      {/* Background blobs */}
      <div className="absolute top-0 left-0 w-72 h-72 rounded-full bg-pixartek-mint/20 blur-3xl pointer-events-none -translate-x-1/3 -translate-y-1/3" />
      <div className="absolute bottom-0 right-0 w-80 h-80 rounded-full bg-pixartek-blush/20 blur-3xl pointer-events-none translate-x-1/3 translate-y-1/3" />

      <div className="relative z-10 w-full max-w-lg">
        {/* Logo */}
        <div className="flex justify-center mb-6 animate-fade-in">
          <PixartekLogo size="sm" />
        </div>

        {/* Achievement */}
        <div className="flex flex-col items-center gap-2 mb-6 animate-scale-in">
          <span className="text-8xl">{achievement.emoji}</span>
          <span className="font-display font-800 text-2xl" style={{ color: achievement.color }}>
            {achievement.label}
          </span>
          {profileName && (
            <p className="font-body text-pixartek-muted">¡Felicidades, {profileName}!</p>
          )}
        </div>

        {/* Artwork info */}
        <h1 className="font-display font-800 text-3xl text-pixartek-ink mb-1 animate-fade-up">{artwork.title}</h1>
        <p className="font-body text-pixartek-muted mb-7 animate-fade-up">{artwork.artist} · {artwork.year}</p>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 mb-7 animate-fade-up">
          <StatCard label="Precisión" value={`${avgPrecision}%`} accent="#E07B6A" highlight={avgPrecision >= 75} />
          <StatCard label="Tiempo total" value={formatTime(elapsed_s)} accent="#7096BC" />
          <StatCard label="Desv. color" value={`ΔE ${avgDeviation}`} accent="#7DC4A8" highlight={Number(avgDeviation) <= 5} />
        </div>

        {/* Per-stage bars */}
        {stageMetrics.length > 0 && (
          <div className="bg-white rounded-2xl p-5 border border-pixartek-border mb-7 shadow-card animate-fade-up">
            <p className="font-display font-600 text-xs text-pixartek-muted uppercase tracking-widest mb-3">
              Resultados por etapa
            </p>
            <div className="flex flex-col gap-2">
              {stageMetrics.map((m, i) => (
                <div key={i} className="flex items-center gap-3">
                  <span className="font-body text-xs text-pixartek-muted w-14 shrink-0 text-right">
                    Etapa {m.stage}
                  </span>
                  <div className="flex-1 h-2 bg-pixartek-cream rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${m.precision_pct}%`,
                        background: "linear-gradient(90deg, #E07B6A, #D4B85A)",
                        transition: "width 0.8s ease",
                      }}
                    />
                  </div>
                  <span className="font-body text-xs text-pixartek-muted w-10 text-right shrink-0">
                    {Math.round(m.precision_pct)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 animate-fade-up">
          <button
            onClick={() => router.push("/catalog")}
            className="
              flex-1 py-4 rounded-2xl font-display font-800 text-base text-white
              bg-pixartek-coral shadow-btn
              hover:opacity-90 active:scale-[0.98] transition-all
            "
          >
            🎨 Elegir otra obra
          </button>
          <button
            onClick={() => router.push("/")}
            className="
              px-6 py-4 rounded-2xl font-display font-600 text-base
              bg-white border-2 border-pixartek-border text-pixartek-ink
              hover:border-pixartek-coral/40 hover:bg-pixartek-cream transition-all
            "
          >
            Inicio
          </button>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, accent, highlight }: {
  label: string; value: string; accent: string; highlight?: boolean;
}) {
  return (
    <div className="bg-white rounded-2xl p-4 flex flex-col items-center gap-1 border border-pixartek-border shadow-card">
      <span
        className="font-display font-800 text-2xl"
        style={{ color: highlight ? accent : "#1A1818" }}
      >
        {value}
      </span>
      <span className="font-body text-xs text-pixartek-muted text-center leading-tight">{label}</span>
    </div>
  );
}
