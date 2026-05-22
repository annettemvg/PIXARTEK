"use client";
import { create } from "zustand";
import type { SessionState, VisionFeedback, NodeStatus, NodeState, StageMetric } from "@/types/session";

const INITIAL_NODES: NodeStatus[] = [
  { id: "rpi5-main",        label: "RPi5 Principal",  state: "ok",      lastSeen: Date.now() },
  { id: "rpi4-projection",  label: "RPi4 Proyección", state: "ok",      lastSeen: Date.now() },
  { id: "rpi4-vision",      label: "RPi4 Visión",     state: "offline", lastSeen: 0 },
];

interface SessionStore extends SessionState {
  init: (artworkId: string, stage: number, total: number) => void;
  nextStage: () => void;
  prevStage: () => void;
  recordStageMetric: () => void;
  setFeedback: (fb: VisionFeedback) => void;
  setNodeState: (id: string, state: NodeState) => void;
  setDispensing: (v: boolean) => void;
  setCleaning: (v: boolean) => void;
  tickElapsed: () => void;
}

export const useSessionStore = create<SessionStore>((set, get) => ({
  artworkId: "",
  currentStage: 1,
  totalStages: 1,
  startedAt: Date.now(),
  elapsed_s: 0,
  feedback: null,
  nodes: INITIAL_NODES,
  projectionActive: false,
  dispensing: false,
  cleaning: false,
  completed: false,
  stageMetrics: [],

  init: (artworkId, stage, total) =>
    set({
      artworkId,
      currentStage: stage,
      totalStages: total,
      startedAt: Date.now(),
      elapsed_s: 0,
      feedback: null,
      projectionActive: true,
      completed: false,
      stageMetrics: [],
    }),

  recordStageMetric: () => {
    const s = get();
    const metric: StageMetric = {
      stage: s.currentStage,
      precision_pct: s.feedback?.precision_pct ?? 0,
      color_deviation: s.feedback?.color_deviation ?? 0,
      elapsed_s: s.elapsed_s,
    };
    set(prev => ({ stageMetrics: [...prev.stageMetrics, metric] }));
  },

  nextStage: () =>
    set(s => {
      const isLast = s.currentStage >= s.totalStages;
      return {
        currentStage: isLast ? s.currentStage : s.currentStage + 1,
        feedback: null,
        completed: isLast,
      };
    }),

  prevStage: () =>
    set(s => ({
      currentStage: Math.max(s.currentStage - 1, 1),
      feedback: null,
    })),

  setFeedback: (fb) => set({ feedback: fb }),

  setNodeState: (id, state) =>
    set(s => ({
      nodes: s.nodes.map(n =>
        n.id === id ? { ...n, state, lastSeen: Date.now() } : n
      ),
    })),

  setDispensing: (v) => set({ dispensing: v }),
  setCleaning:   (v) => set({ cleaning: v }),
  tickElapsed:   ()  => set(s => ({ elapsed_s: s.elapsed_s + 1 })),
}));

// Mock: simulate incoming vision feedback every 5 seconds
export function startMockFeedback(store: SessionStore) {
  const MOCK_FEEDBACKS: VisionFeedback[] = [
    {
      precision_pct: 87,
      color_deviation: 4.2,
      stroke_errors: [{ zone: "superior-izquierda", message: "Trazo demasiado grueso" }],
      suggestions: ["Usa menos presión en la brocha", "Mantén el ángulo a 45°"],
      timestamp: Date.now(),
    },
    {
      precision_pct: 92,
      color_deviation: 2.1,
      stroke_errors: [],
      suggestions: ["¡Excelente trazo! Continúa con la misma técnica"],
      timestamp: Date.now(),
    },
    {
      precision_pct: 74,
      color_deviation: 8.7,
      stroke_errors: [
        { zone: "centro", message: "Color desviado — mezcla más azul" },
        { zone: "borde-derecho", message: "Zona sin cubrir" },
      ],
      suggestions: ["Agrega más pigmento azul ultramar", "Cubre el borde derecho primero"],
      timestamp: Date.now(),
    },
  ];

  let i = 0;
  return setInterval(() => {
    store.setFeedback({ ...MOCK_FEEDBACKS[i % MOCK_FEEDBACKS.length], timestamp: Date.now() });
    i++;
  }, 5000);
}
