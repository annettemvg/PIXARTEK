"use client";
import type { Artwork } from "@/types/artwork";
import { DIFFICULTY_LABEL, DIFFICULTY_COLOR } from "@/lib/mock-artworks";
import { clsx } from "clsx";

interface Props {
  artwork: Artwork;
  selected: boolean;
  onClick: () => void;
}

export default function ArtworkCard({ artwork, selected, onClick }: Props) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        "relative flex flex-col text-left rounded-2xl overflow-hidden border-2 transition-all duration-200 bg-white",
        "hover:scale-[1.03] hover:shadow-hover active:scale-[0.98] cursor-pointer select-none",
        selected
          ? "border-pixartek-coral shadow-hover"
          : "border-pixartek-border shadow-card hover:border-pixartek-coral/40"
      )}
    >
      {/* Thumbnail */}
      <div
        className="h-40 w-full relative flex items-end justify-start p-3 overflow-hidden"
        style={{ backgroundColor: artwork.color }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={artwork.image}
          alt={artwork.title}
          className="absolute inset-0 w-full h-full object-cover"
          loading="lazy"
          onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
        />
        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
        <span className={clsx(
          "relative z-10 text-xs font-body font-700 border rounded-full px-2.5 py-0.5 bg-white/90 backdrop-blur-sm",
          DIFFICULTY_COLOR[artwork.difficulty]
        )}>
          {DIFFICULTY_LABEL[artwork.difficulty]}
        </span>
      </div>

      {/* Info */}
      <div className="bg-white p-4 flex flex-col gap-1.5">
        <h3 className="font-display font-700 text-base leading-tight text-pixartek-ink">{artwork.title}</h3>
        <p className="font-body text-sm text-pixartek-muted">{artwork.artist} · {artwork.year}</p>
        <div className="flex gap-3 mt-1 text-xs text-pixartek-muted font-body">
          <span>🎨 {artwork.stages.length} etapas</span>
          <span>⏱ {artwork.duration_min} min</span>
        </div>
      </div>

      {/* Selected check */}
      {selected && (
        <div className="absolute top-3 right-3 w-7 h-7 rounded-full bg-pixartek-coral flex items-center justify-center text-white text-sm font-bold shadow-btn">
          ✓
        </div>
      )}
    </button>
  );
}
