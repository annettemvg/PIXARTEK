"use client";
import { useRef, useCallback } from "react";
import { createSession, advanceStage, recordMetric, apiDispense, apiClean } from "@/lib/api-client";

export function useSessionApi() {
  const sessionIdRef = useRef<string | null>(null);

  const initSession = useCallback(async (artworkId: string, stage: number, total: number) => {
    try {
      const data = await createSession(artworkId, stage, total);
      sessionIdRef.current = data.id;
    } catch {
      // API offline — run in demo mode without persisting
      sessionIdRef.current = null;
    }
  }, []);

  const nextStage = useCallback(async (stage: number) => {
    if (!sessionIdRef.current) return;
    try {
      await advanceStage(sessionIdRef.current, stage);
    } catch { /* offline — ignore */ }
  }, []);

  const saveMetric = useCallback(async (data: {
    stage: number;
    precision_pct: number;
    color_deviation: number;
    elapsed_s: number;
    feedback_json?: object;
  }) => {
    if (!sessionIdRef.current) return;
    try {
      await recordMetric(sessionIdRef.current, data);
    } catch { /* offline — ignore */ }
  }, []);

  const dispense = useCallback(async (slot = 1, artworkId = "") => {
    try {
      await apiDispense(slot, 500, artworkId);
    } catch { /* offline — ignore */ }
  }, []);

  const clean = useCallback(async () => {
    try {
      await apiClean();
    } catch { /* offline — ignore */ }
  }, []);

  return { sessionId: sessionIdRef, initSession, nextStage, saveMetric, dispense, clean };
}
