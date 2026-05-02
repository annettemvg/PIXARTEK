"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import ArtworkCard from "@/components/ui/ArtworkCard";
import PixartekLogo from "@/components/ui/PixartekLogo";
import { DIFFICULTY_LABEL, DIFFICULTY_COLOR } from "@/lib/mock-artworks";
import { useArtworks } from "@/hooks/useArtworks";
import { useProfileStore } from "@/lib/profile-store";
import { getStageImageUrl, projectStage } from "@/lib/api-client";
import type { Artwork } from "@/types/artwork";
import { clsx } from "clsx";

type Filter = "all" | "beginner" | "intermediate" | "advanced";

const FILTER_COLORS: Record<Filter, string> = {
  all:          "bg-pixartek-ink text-white border-pixartek-ink",
  beginner:     "bg-emerald-500 text-white border-emerald-500",
  intermediate: "bg-amber-500 text-white border-amber-500",
  advanced:     "bg-rose-500 text-white border-rose-500",
};

export default function CatalogPage() {
  const router = useRouter();
  const { artworks, loading } = useArtworks();
  const { profile } = useProfileStore();
  const [selected, setSelected] = useState<Artwork | null>(null);
  const [selectedStage, setSelectedStage] = useState<number>(1);
  const [filter, setFilter] = useState<Filter>("all");

  const filtered = filter === "all" ? artworks : artworks.filter(a => a.difficulty === filter);

  function handleSelect(artwork: Artwork) {
    setSelected(artwork);
    setSelectedStage(1);
  }

  async function handleStart() {
    if (!selected) return;
    // Project the selected stage on the projector before navigating
    try {
      await projectStage(selected.id, selectedStage);
    } catch {
      // Projection failure is non-blocking
    }
    router.push(`/session?artwork=${selected.id}&stage=${selectedStage}`);
  }

  return (
    <div className="flex h-screen overflow-hidden bg-pixartek-cream">

      {/* ── Left panel ── */}
      <div className="flex-1 flex flex-col overflow-hidden">

        {/* Header */}
        <header className="flex items-center justify-between px-8 py-4 bg-white border-b border-pixartek-border shrink-0">
          <div className="flex items-center gap-5">
            <button onClick={() => router.push("/")} className="hover:opacity-70 transition">
              <PixartekLogo size="sm" />
            </button>
            <div className="h-6 w-px bg-pixartek-border" />
            <h1 className="font-display font-700 text-xl text-pixartek-ink">
              Catálogo de Obras
            </h1>
          </div>

          <div className="flex items-center gap-3">
            {/* Filters */}
            {(["all", "beginner", "intermediate", "advanced"] as Filter[]).map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={clsx(
                  "px-4 py-1.5 rounded-full text-sm font-body font-600 border-2 transition-all duration-150",
                  filter === f
                    ? FILTER_COLORS[f]
                    : "bg-white border-pixartek-border text-pixartek-muted hover:border-pixartek-ink/40"
                )}
              >
                {f === "all" ? "Todas" : DIFFICULTY_LABEL[f]}
              </button>
            ))}

            <div className="h-6 w-px bg-pixartek-border mx-1" />

            {/* User chip */}
            {profile && (
              <div className="flex items-center gap-2 bg-pixartek-cream border border-pixartek-border rounded-full px-3 py-1.5">
                <span className="text-lg">{profile.avatar}</span>
                <span className="font-body font-600 text-sm text-pixartek-ink">{profile.name}</span>
              </div>
            )}

            <button
              onClick={() => router.push("/settings")}
              className="w-9 h-9 flex items-center justify-center rounded-full border-2 border-pixartek-border text-pixartek-muted hover:border-pixartek-ink/40 hover:text-pixartek-ink transition"
              title="Configuración"
            >
              ⚙
            </button>
          </div>
        </header>

        {/* Grid */}
        <div className="flex-1 scroll-area px-8 py-7">
          {loading ? (
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-5">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="h-56 rounded-2xl bg-white border-2 border-pixartek-border animate-pulse"
                />
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-4 text-pixartek-muted">
              <span className="text-6xl">🖼</span>
              <p className="font-body text-lg">No hay obras en esta categoría</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-5">
              {filtered.map(artwork => (
                <ArtworkCard
                  key={artwork.id}
                  artwork={artwork}
                  selected={selected?.id === artwork.id}
                  onClick={() => handleSelect(artwork)}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── Right detail panel ── */}
      <div className="w-88 shrink-0 border-l border-pixartek-border flex flex-col bg-white"
           style={{ width: "340px" }}>
        {selected ? (
          <>
            {/* Artwork preview */}
            <div className="p-6 border-b border-pixartek-border">
              <div
                className="w-full h-44 rounded-2xl mb-4 overflow-hidden relative shadow-card"
                style={{ backgroundColor: selected.color }}
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={selected.image}
                  alt={selected.title}
                  className="absolute inset-0 w-full h-full object-cover"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                />
              </div>

              <h2 className="font-display font-700 text-xl text-pixartek-ink">{selected.title}</h2>
              <p className="font-body text-pixartek-muted text-sm mt-1">{selected.artist} · {selected.year}</p>

              <div className="flex items-center gap-2 mt-3 flex-wrap">
                <span className={clsx(
                  "text-xs font-body font-700 border-2 rounded-full px-3 py-0.5",
                  DIFFICULTY_COLOR[selected.difficulty]
                )}>
                  {DIFFICULTY_LABEL[selected.difficulty]}
                </span>
                <span className="text-xs text-pixartek-muted font-body">
                  🎨 {selected.stages.length} etapas · ⏱ {selected.duration_min} min
                </span>
              </div>

              <div className="flex gap-2 mt-3 flex-wrap">
                {selected.tags.map(tag => (
                  <span key={tag}
                    className="text-xs bg-pixartek-cream border border-pixartek-border rounded-full px-2.5 py-0.5 text-pixartek-muted font-body">
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            {/* Stage selector */}
            <div className="flex-1 scroll-area p-5">
              <p className="font-display font-600 text-xs text-pixartek-muted uppercase tracking-widest mb-3">
                Selecciona la etapa
              </p>
              <div className="flex flex-col gap-2">
                {selected.stages.map((stage: Artwork["stages"][0]) => (
                  <button
                    key={stage.number}
                    onClick={() => setSelectedStage(stage.number)}
                    className={clsx(
                      "flex items-start gap-3 p-3 rounded-xl border-2 text-left transition-all duration-150",
                      selectedStage === stage.number
                        ? "border-pixartek-coral bg-pixartek-coral/5 shadow-card"
                        : "border-pixartek-border bg-white hover:border-pixartek-coral/30 hover:bg-pixartek-cream/60"
                    )}
                  >
                    {/* Stage thumbnail */}
                    <div
                      className="w-12 h-12 rounded-xl overflow-hidden shrink-0 border-2 border-pixartek-border"
                      style={{ backgroundColor: selected.color }}
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={stage.image ?? getStageImageUrl(selected.id, stage.number)}
                        alt={`Etapa ${stage.number}`}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          const t = e.target as HTMLImageElement;
                          const fallback = getStageImageUrl(selected.id, stage.number);
                          if (!t.src.includes("/api/stages/")) t.src = fallback;
                          else t.style.display = "none";
                        }}
                      />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className={clsx(
                          "w-5 h-5 rounded-full flex items-center justify-center text-xs font-display font-700 shrink-0",
                          selectedStage === stage.number
                            ? "bg-pixartek-coral text-white"
                            : "bg-pixartek-cream text-pixartek-muted"
                        )}>
                          {stage.number}
                        </span>
                        <p className="font-body font-600 text-sm text-pixartek-ink truncate">{stage.title}</p>
                      </div>
                      <p className="text-xs text-pixartek-muted font-body line-clamp-2 leading-relaxed">
                        {stage.description}
                      </p>
                      <p className="text-xs text-pixartek-muted/60 font-body mt-1">⏱ {stage.duration_min} min</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* CTA */}
            <div className="p-5 border-t border-pixartek-border bg-white">
              <button
                onClick={handleStart}
                className="
                  w-full py-4 rounded-2xl font-display font-800 text-lg text-white
                  bg-pixartek-coral shadow-btn
                  hover:opacity-90 active:scale-[0.99] transition-all duration-150
                "
              >
                ¡Pintar ahora! →
              </button>
              <p className="text-xs text-pixartek-muted font-body text-center mt-2">
                Etapa {selectedStage} de {selected.stages.length} · {selected.stages[selectedStage - 1]?.duration_min} min estimados
              </p>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-pixartek-muted px-8 text-center gap-4">
            <span className="text-7xl">🎨</span>
            <p className="font-display font-600 text-lg text-pixartek-ink">Elige una obra</p>
            <p className="font-body text-sm leading-relaxed">
              Selecciona cualquier pintura del catálogo para ver sus etapas y comenzar a pintar
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
