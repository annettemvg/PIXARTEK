"use client";
import { useEffect, useRef, useCallback, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { clsx } from "clsx";
import { useSessionStore } from "@/lib/session-store";
import { useProfileStore } from "@/lib/profile-store";
import { useSessionApi } from "@/hooks/useSession";
import { useArtworks } from "@/hooks/useArtworks";
import { useWebSocket, type WsMessage } from "@/hooks/useWebSocket";
import { ARTWORKS } from "@/lib/mock-artworks";
import { getStageImageUrl, projectStage } from "@/lib/api-client";
import PixartekLogo from "@/components/ui/PixartekLogo";
import FeedbackPanel from "@/components/kiosk/FeedbackPanel";
import NodeStatus from "@/components/kiosk/NodeStatus";
import HardwareControls from "@/components/kiosk/HardwareControls";
import CompletionScreen from "@/components/kiosk/CompletionScreen";
import FeedbackOverlay, { type FeedbackType } from "@/components/feedback/FeedbackOverlay";
import VisionAnalysisModal from "@/components/ui/VisionAnalysisModal";
import type { NodeState } from "@/types/session";

function formatTime(s: number) {
  const m = Math.floor(s / 60).toString().padStart(2, "0");
  const sec = (s % 60).toString().padStart(2, "0");
  return `${m}:${sec}`;
}

function SessionContent() {
  const router = useRouter();
  const params = useSearchParams();
  const artworkId = params.get("artwork") ?? "";
  const startStage = parseInt(params.get("stage") ?? "1", 10);

  const store = useSessionStore();
  const api = useSessionApi();
  const { artworks } = useArtworks();
  const { profile } = useProfileStore();
  const [stageImgError, setStageImgError] = useState(false);
  const [feedbackOverlay, setFeedbackOverlay] = useState<{ type: FeedbackType; message?: string } | null>(null);

  const timerRef  = useRef<ReturnType<typeof setInterval> | null>(null);
  const metricRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const hasRealFeedbackRef = useRef(false);

  const handleWsMessage = useCallback((msg: WsMessage) => {
    if (msg.topic === "pixartek/vision/feedback") {
      const p = msg.payload;
      hasRealFeedbackRef.current = true;
      store.setFeedback({
        precision_pct:   (p.precision_pct   as number) ?? 0,
        color_deviation: (p.color_deviation as number) ?? 0,
        stroke_errors:   (p.stroke_errors   as { zone: string; message: string }[]) ?? [],
        suggestions:     (p.suggestions     as string[]) ?? [],
        timestamp:       (p.timestamp       as number) ?? Date.now(),
      });

      // Determine feedback type
      const errors = (p.stroke_errors as { zone: string; message: string }[]) ?? [];
      const suggestions = (p.suggestions as string[]) ?? [];
      const precision = (p.precision_pct as number) ?? 0;

      if (errors.length > 0) {
        setFeedbackOverlay({ type: "corrección", message: errors[0]?.message });
      } else if (suggestions.length > 0) {
        setFeedbackOverlay({ type: "sugerencia", message: suggestions[0] });
      } else if (precision > 85) {
        setFeedbackOverlay({ type: "correcto" });
      }
    }
    if (msg.topic === "pixartek/system/heartbeat") {
      store.setNodeState(msg.payload.node as string, (msg.payload.status as NodeState) ?? "ok");
    }
    if (msg.topic === "pixartek/projection/status") {
      const active = msg.payload.active as boolean;
      if (active !== undefined) useSessionStore.setState({ projectionActive: active });
    }
  }, [store]);

  const { status: wsStatus } = useWebSocket({ onMessage: handleWsMessage });
  const artwork = artworks.find(a => a.id === artworkId) ?? ARTWORKS.find(a => a.id === artworkId);

  useEffect(() => {
    if (!artwork) return;
    store.init(artworkId, startStage, artwork.stages.length);
    api.initSession(artworkId, startStage, artwork.stages.length);
    timerRef.current = setInterval(() => store.tickElapsed(), 1000);
    metricRef.current = setInterval(() => {
      const fb = useSessionStore.getState().feedback;
      const elapsed = useSessionStore.getState().elapsed_s;
      const stage = useSessionStore.getState().currentStage;
      if (fb) api.saveMetric({ stage, precision_pct: fb.precision_pct, color_deviation: fb.color_deviation, elapsed_s: elapsed, feedback_json: { stroke_errors: fb.stroke_errors, suggestions: fb.suggestions } });
    }, 30000);
    projectStage(artworkId, startStage);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (metricRef.current) clearInterval(metricRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [artworkId]);

  useEffect(() => { setStageImgError(false); }, [store.currentStage]);

  if (!artwork) {
    return (
      <div className="flex items-center justify-center h-screen bg-pixartek-cream">
        <div className="text-center">
          <p className="font-body text-pixartek-muted mb-4">Obra no encontrada.</p>
          <button onClick={() => router.push("/catalog")}
            className="px-6 py-3 rounded-xl bg-pixartek-coral text-white font-display font-700 hover:opacity-90 transition">
            ← Volver al catálogo
          </button>
        </div>
      </div>
    );
  }

  if (store.completed) {
    return <CompletionScreen artwork={artwork} stageMetrics={store.stageMetrics} elapsed_s={store.elapsed_s} profileName={profile?.name} />;
  }

  const stage = artwork.stages[store.currentStage - 1];
  const progressPct = ((store.currentStage - 1) / artwork.stages.length) * 100;
  const currentStageImgUrl = getStageImageUrl(artworkId, store.currentStage);

  async function handleNextStage() {
    store.recordStageMetric();
    const isLast = store.currentStage >= store.totalStages;
    const nextStageNum = store.currentStage + 1;
    store.nextStage();
    if (!isLast) { await api.nextStage(nextStageNum); projectStage(artworkId, nextStageNum); }
  }
  async function handlePrevStage() {
    const prev = store.currentStage - 1;
    if (prev >= 1) { store.prevStage(); projectStage(artworkId, prev); }
  }
  async function handleDispense() { store.setDispensing(true); await api.dispense(); setTimeout(() => store.setDispensing(false), 3000); }
  async function handleClean() { store.setCleaning(true); await api.clean(); setTimeout(() => store.setCleaning(false), 2500); }

  return (
    <div className="flex flex-col h-screen bg-pixartek-cream overflow-hidden">

      {/* ── Header ── */}
      <header className="flex items-center justify-between px-5 py-3 bg-white border-b border-pixartek-border shrink-0">
        <div className="flex items-center gap-4">
          <button onClick={() => router.push("/catalog")} className="hover:opacity-70 transition">
            <PixartekLogo size="sm" />
          </button>
          <div className="h-5 w-px bg-pixartek-border" />
          <div>
            <h1 className="font-display font-700 text-base text-pixartek-ink leading-tight">{artwork.title}</h1>
            <p className="font-body text-xs text-pixartek-muted">{artwork.artist} · {artwork.year}</p>
          </div>
          {profile && (
            <div className="flex items-center gap-1.5 bg-pixartek-cream border border-pixartek-border px-2.5 py-1 rounded-full font-body text-xs">
              {profile.avatar} <span className="font-600 text-pixartek-ink">{profile.name}</span>
            </div>
          )}
          <div className={clsx(
            "flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border font-body",
            wsStatus === "connected"  ? "border-emerald-300 text-emerald-600 bg-emerald-50" :
            wsStatus === "connecting" ? "border-amber-300 text-amber-600 bg-amber-50" :
                                        "border-pixartek-border text-pixartek-muted"
          )}>
            <span className={clsx("w-1.5 h-1.5 rounded-full",
              wsStatus === "connected" ? "bg-emerald-500 animate-pulse" :
              wsStatus === "connecting" ? "bg-amber-500 animate-pulse" : "bg-pixartek-border"
            )} />
            {wsStatus === "connected" ? "Live" : wsStatus === "connecting" ? "Conectando…" : "Sin señal"}
          </div>
        </div>

        {/* Progress */}
        <div className="flex-1 mx-8 max-w-sm">
          <div className="flex justify-between mb-1">
            <span className="font-body text-xs text-pixartek-muted">Etapa {store.currentStage} / {store.totalStages}</span>
            <span className="font-body text-xs text-pixartek-muted">⏱ {formatTime(store.elapsed_s)}</span>
          </div>
          <div className="h-2 bg-pixartek-border rounded-full overflow-hidden">
            <div className="h-full rounded-full transition-all duration-500"
              style={{ width: `${progressPct}%`, background: "linear-gradient(90deg,#E07B6A,#D4B85A,#7DC4A8)" }} />
          </div>
          <div className="flex mt-1.5 gap-0.5">
            {artwork.stages.map(s => (
              <div key={s.number} className={clsx("flex-1 h-1 rounded-full transition-colors",
                s.number < store.currentStage ? "bg-pixartek-coral" :
                s.number === store.currentStage ? "bg-pixartek-coral/40" : "bg-pixartek-border")} />
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button onClick={() => router.push("/settings")}
            className="w-9 h-9 flex items-center justify-center rounded-full border-2 border-pixartek-border text-pixartek-muted hover:border-pixartek-ink/40 transition">
            ⚙
          </button>
          <button onClick={handlePrevStage} disabled={store.currentStage === 1}
            className="px-4 py-2 rounded-xl border-2 border-pixartek-border font-body font-600 text-sm text-pixartek-muted hover:border-pixartek-coral/40 disabled:opacity-30 disabled:cursor-not-allowed transition">
            ‹ Anterior
          </button>
          <button onClick={handleNextStage}
            className="px-5 py-2 rounded-xl font-display font-700 text-sm text-white bg-pixartek-coral shadow-btn hover:opacity-90 active:scale-[0.98] transition">
            {store.currentStage === store.totalStages ? "Finalizar ✓" : "Siguiente ›"}
          </button>
        </div>
      </header>

      {/* ── Body ── */}
      <div className="flex flex-1 overflow-hidden">

        {/* Left sidebar */}
        <div className="w-72 border-r border-pixartek-border flex flex-col shrink-0 bg-white scroll-area">
          {/* Top section: Image + Title (pinned) */}
          <div className="p-4 border-b border-pixartek-border shrink-0">
            <p className="font-display font-600 text-xs text-pixartek-muted uppercase tracking-widest mb-2">Etapa Actual</p>
            <div className="w-full aspect-square rounded-xl overflow-hidden border border-pixartek-border mb-3" style={{ backgroundColor: artwork.color }}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={currentStageImgUrl} alt={`Etapa ${store.currentStage}`} className="w-full h-full object-cover" />
            </div>
            <p className="font-display font-700 text-sm text-pixartek-coral uppercase tracking-wide">
              {stage.title}
            </p>
          </div>

          {/* Scrollable content */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-4 border-b border-pixartek-border">
              <p className="font-display font-600 text-xs text-pixartek-muted uppercase tracking-widest mb-2">Objetivo</p>
              <p className="font-body text-xs text-pixartek-ink leading-relaxed">{stage.objective || stage.description}</p>
              <p className="font-body text-xs text-pixartek-muted/50 mt-2">⏱ {stage.duration_min} min</p>
            </div>

            <div className="p-4 border-b border-pixartek-border">
              <p className="font-display font-600 text-xs text-pixartek-muted uppercase tracking-widest mb-2">Colores</p>
              <div className="flex flex-wrap gap-1.5">
                {(stage.colors || []).map((color, i) => (
                  <span key={i} className="px-2 py-1 bg-pixartek-cream text-pixartek-ink rounded text-xs border border-pixartek-border font-body">
                    {color}
                  </span>
                ))}
              </div>
            </div>

            <div className="p-4 border-b border-pixartek-border">
              <p className="font-display font-600 text-xs text-pixartek-muted uppercase tracking-widest mb-2">Materiales</p>
              <ul className="text-xs text-pixartek-ink font-body space-y-1">
                {(stage.materials || []).map((material, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-pixartek-coral mt-0.5">•</span>
                    <span>{material}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-4 border-b border-pixartek-border">
              <p className="font-display font-600 text-xs text-pixartek-muted uppercase tracking-widest mb-2">Brochas</p>
              <ul className="text-xs text-pixartek-ink font-body space-y-1">
                {(stage.brushes || []).map((brush, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-pixartek-coral mt-0.5">•</span>
                    <span>{brush}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-4">
              <p className="font-display font-600 text-xs text-pixartek-muted uppercase tracking-widest mb-3">Todas las etapas</p>
              <div className="space-y-1">
                {artwork.stages.map(s => (
                  <div key={s.number} className={clsx(
                    "flex items-center gap-2 px-3 py-2 rounded text-xs font-body transition cursor-pointer hover:bg-pixartek-cream/50 border",
                    s.number === store.currentStage ? "bg-pixartek-coral/15 text-pixartek-coral font-700 border-pixartek-coral/30" :
                    s.number < store.currentStage   ? "text-pixartek-muted/40 line-through border-pixartek-border/30" : "text-pixartek-muted border-pixartek-border/50"
                  )}>
                    <span className={clsx("w-5 h-5 rounded-full flex items-center justify-center text-xs font-display font-700 shrink-0 text-white",
                      s.number < store.currentStage  ? "bg-pixartek-mint" :
                      s.number === store.currentStage ? "bg-pixartek-coral" : "bg-pixartek-border")}>
                      {s.number < store.currentStage ? "✓" : s.number}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="truncate font-600">{s.title}</p>
                      <p className="text-xs opacity-60">{s.duration_min} min</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Center image */}
        <div className="flex-1 flex flex-col bg-[#EDEAE5] relative overflow-hidden">
          {stageImgError ? (
            <div className="w-full h-full flex items-center justify-center">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={artwork.image} alt={artwork.title} className="w-full h-full object-contain opacity-40" />
            </div>
          ) : (
            /* eslint-disable-next-line @next/next/no-img-element */
            <img key={store.currentStage} src={currentStageImgUrl} alt={`Etapa ${store.currentStage}`}
              className="w-full h-full object-contain" onError={() => setStageImgError(true)} />
          )}
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/55 to-transparent px-6 py-5 flex items-end justify-between">
            <div>
              <p className="font-body text-xs text-white/60 uppercase tracking-wide mb-0.5">
                Etapa {store.currentStage} de {store.totalStages}
              </p>
              <p className="font-display font-700 text-white text-lg">{stage.title}</p>
            </div>
            <div className={clsx("flex items-center gap-2 px-3 py-1.5 rounded-full text-xs border font-body",
              store.projectionActive
                ? "border-emerald-400/50 text-emerald-300 bg-emerald-900/30"
                : "border-white/20 text-white/40 bg-black/20")}>
              <span className={clsx("w-1.5 h-1.5 rounded-full",
                store.projectionActive ? "bg-emerald-400 animate-pulse" : "bg-white/30")} />
              {store.projectionActive ? "Proyección activa" : "Proyección inactiva"}
            </div>
          </div>
        </div>

        {/* Right panel */}
        <div className="w-72 border-l border-pixartek-border flex flex-col shrink-0 bg-white scroll-area">
          <div className="p-4 border-b border-pixartek-border">
            <p className="font-display font-600 text-xs text-pixartek-muted uppercase tracking-widest mb-3">Análisis de visión</p>
            <VisionAnalysisModal />
          </div>
          <div className="p-4 border-b border-pixartek-border">
            <p className="font-display font-600 text-xs text-pixartek-muted uppercase tracking-widest mb-3">Retroalimentación</p>
            <FeedbackPanel feedback={store.feedback} />
          </div>
          <div className="p-4 border-b border-pixartek-border">
            <p className="font-display font-600 text-xs text-pixartek-muted uppercase tracking-widest mb-3">Hardware</p>
            <HardwareControls dispensing={store.dispensing} cleaning={store.cleaning} onDispense={handleDispense} onClean={handleClean} />
          </div>
          <div className="p-4">
            <p className="font-display font-600 text-xs text-pixartek-muted uppercase tracking-widest mb-3">Estado de nodos</p>
            <NodeStatus nodes={store.nodes} />
          </div>
        </div>
      </div>

      {/* Feedback Overlay */}
      {feedbackOverlay && (
        <FeedbackOverlay
          type={feedbackOverlay.type}
          visible={!!feedbackOverlay}
          onClose={() => setFeedbackOverlay(null)}
          message={feedbackOverlay.message}
        />
      )}
    </div>
  );
}

export default function SessionPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-screen bg-pixartek-cream">
        <p className="font-body text-pixartek-muted text-lg animate-pulse">Cargando sesión…</p>
      </div>
    }>
      <SessionContent />
    </Suspense>
  );
}
