"use client";
import { useCallback, useRef } from "react";

export type VoiceLevel = "niño" | "principiante" | "intermedio" | "avanzado";

const BASE = typeof window !== "undefined"
  ? `http://${window.location.hostname}:8000`
  : "http://localhost:8000";

export function usePixiVoice(_level: VoiceLevel = "principiante") {
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const speak = useCallback(async (text: string) => {
    // Stop any currently playing audio
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = "";
      audioRef.current = null;
    }

    // Clean markdown before sending
    const clean = text
      .replace(/\*\*/g, "")
      .replace(/^\d+\.\s/gm, "")
      .replace(/^[-*]\s/gm, "")
      .replace(/#/g, "")
      .trim()
      .slice(0, 500); // cap for credit safety

    try {
      const res = await fetch(`${BASE}/api/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: clean }),
      });

      if (!res.ok) return;

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => URL.revokeObjectURL(url);
      audio.play();
    } catch {
      // ElevenLabs unavailable — silent fallback
    }
  }, []);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = "";
      audioRef.current = null;
    }
  }, []);

  return { speak, stop };
}

export function useVoiceInput(onResult: (text: string) => void, onListening: (active: boolean) => void) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recogRef = useRef<any>(null);

  const startListening = useCallback(() => {
    if (typeof window === "undefined") return;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const w = window as any;
    const SpeechRecognition = w.SpeechRecognition ?? w.webkitSpeechRecognition;
    if (!SpeechRecognition) { alert("Tu navegador no soporta reconocimiento de voz."); return; }

    const recog = new SpeechRecognition();
    recog.lang = "es-US";
    recog.interimResults = false;
    recog.maxAlternatives = 1;
    recogRef.current = recog;

    recog.onstart = () => onListening(true);
    recog.onend = () => onListening(false);
    recog.onerror = () => onListening(false);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    recog.onresult = (e: any) => { onResult(e.results[0][0].transcript); };
    recog.start();
  }, [onResult, onListening]);

  const stopListening = useCallback(() => { recogRef.current?.stop(); }, []);

  return { startListening, stopListening };
}
