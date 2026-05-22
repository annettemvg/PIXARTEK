"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import { clsx } from "clsx";
import { usePixiVoice, useVoiceInput } from "@/hooks/usePixiVoice";
import { useAuthStore } from "@/lib/auth-store";
import { useSessionStore } from "@/lib/session-store";

interface Message {
  role: "user" | "model";
  content: string;
}

interface Props {
  artworkTitle?: string;
  artworkArtist?: string;
  stageTitle?: string;
  stageNumber?: number;
  silent?: boolean;
}

const BASE = typeof window !== "undefined"
  ? `http://${window.location.hostname}:8000`
  : "http://localhost:8000";

const WS_URL = typeof window !== "undefined"
  ? `ws://${window.location.hostname}:8000/ws`
  : "ws://localhost:8000/ws";

function renderInline(text: string): React.ReactNode {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith("**") && part.endsWith("**")
      ? <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong>
      : part
  );
}

function renderMessage(text: string) {
  const lines = text.split("\n").filter((l, i, arr) => !(l.trim() === "" && arr[i - 1]?.trim() === ""));
  const elements: React.ReactNode[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (line.match(/^\d+\.\s+/)) {
      const items: string[] = [];
      while (i < lines.length && lines[i].match(/^\d+\.\s+/)) { items.push(lines[i].replace(/^\d+\.\s+/, "")); i++; }
      elements.push(<ol key={`ol-${i}`} className="list-decimal list-outside ml-4 space-y-0.5 my-1">{items.map((item, j) => <li key={j}>{renderInline(item)}</li>)}</ol>);
      continue;
    }
    if (line.match(/^[-*]\s+/)) {
      const items: string[] = [];
      while (i < lines.length && lines[i].match(/^[-*]\s+/)) { items.push(lines[i].replace(/^[-*]\s+/, "")); i++; }
      elements.push(<ul key={`ul-${i}`} className="list-disc list-outside ml-4 space-y-0.5 my-1">{items.map((item, j) => <li key={j}>{renderInline(item)}</li>)}</ul>);
      continue;
    }
    if (line.trim() === "") { elements.push(<div key={`sp-${i}`} className="h-1" />); i++; continue; }
    elements.push(<p key={`p-${i}`} className="leading-relaxed">{renderInline(line)}</p>);
    i++;
  }
  return <div className="space-y-1 text-xs">{elements}</div>;
}

type VoiceState = "idle" | "listening" | "thinking" | "speaking";

export default function PixiEmbedded({ artworkTitle, artworkArtist, stageTitle, stageNumber, silent = false }: Props) {
  const { user } = useAuthStore();
  const userLevel = user?.level ?? "principiante";
  const approveStage = useSessionStore(s => s.approveStage);

  const [history, setHistory] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [listening, setListening] = useState(false);
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [muted, setMuted] = useState(silent);
  const mutedRef = useRef(silent);
  const setMutedBoth = (v: boolean) => { mutedRef.current = v; setMuted(v); };

  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { speak, stop } = usePixiVoice(userLevel);

  const handleVoiceResult = useCallback((text: string) => {
    setInput(text);
    setTimeout(() => inputRef.current?.focus(), 50);
  }, []);

  const { startListening, stopListening } = useVoiceInput(handleVoiceResult, (active) => {
    setListening(active);
    setVoiceState(active ? "listening" : "idle");
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, loading, analyzing]);

  // Stop speaking when the component unmounts (user leaves the artwork)
  useEffect(() => {
    return () => { stop(); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const triggerGreeting = useCallback(async () => {
    setMutedBoth(false);
    if (silent) {
      // Presentation mode: trigger analysis correction instead of greeting
      setAnalyzing(true);
      setVoiceState("thinking");
      try {
        const res = await fetch(`${BASE}/api/chat/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ artwork_title: artworkTitle, stage_title: stageTitle, stage_number: stageNumber }),
        });
        const data = await res.json();
        setVoiceState("speaking");
        setHistory([{ role: "model", content: data.reply }]);
        speak(data.reply);
        setTimeout(() => setVoiceState("idle"), 4000);
      } catch {
        setVoiceState("idle");
        setHistory([{ role: "model", content: "No pude analizar ahora." }]);
      } finally {
        setAnalyzing(false);
      }
    } else {
      const name = user?.name?.split(" ")[0] ?? "artista";
      const greeting = artworkTitle
        ? `¡Hola ${name}! Lista para guiarte con ${artworkTitle}. ¡Vamos!`
        : `¡Hola ${name}! Soy Pixi. ¿En qué te ayudo?`;
      setHistory([{ role: "model", content: greeting }]);
      speak(greeting);
    }
  }, [artworkTitle, stageTitle, stageNumber, user, silent, speak, analyzing]);

  useEffect(() => {
    if (!silent) triggerGreeting();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);

        // In presentation mode, NEVER process auto-messages — only manual VER clicks allowed
        if (silent) return;

        // Regular Pixi feedback message
        if (msg.topic === "pixi/auto_feedback" && msg.payload?.reply) {
          setAnalyzing(false);
          setVoiceState("speaking");
          setHistory(h => [...h, { role: "model", content: msg.payload.reply }]);
          if (voiceEnabled) speak(msg.payload.reply);
          setTimeout(() => setVoiceState("idle"), 4000);
        }

        // Pixi approves advancing to next stage
        if (msg.topic === "pixi/stage_approved" && msg.payload?.reply) {
          approveStage();
          setVoiceState("speaking");
          setHistory(h => [...h, { role: "model", content: msg.payload.reply }]);
          if (voiceEnabled) speak(msg.payload.reply);
          setTimeout(() => setVoiceState("idle"), 4000);
        }
      } catch {}
    };
    return () => ws.close();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [voiceEnabled]);

  const analyzeCanvas = useCallback(async () => {
    if (analyzing || loading) return;
    setAnalyzing(true);
    setVoiceState("thinking");
    setHistory(h => [...h, { role: "user", content: "Analiza mi técnica ahora" }]);
    try {
      const res = await fetch(`${BASE}/api/chat/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ artwork_title: artworkTitle, stage_title: stageTitle, stage_number: stageNumber }),
      });
      const data = await res.json();
      setVoiceState("speaking");
      setHistory(h => [...h, { role: "model", content: data.reply }]);
      if (voiceEnabled && !mutedRef.current) speak(data.reply);
      setTimeout(() => setVoiceState("idle"), 4000);
    } catch {
      setVoiceState("idle");
      setHistory(h => [...h, { role: "model", content: "No pude acceder a la cámara ahora." }]);
    } finally {
      setAnalyzing(false);
    }
  }, [analyzing, loading, artworkTitle, stageTitle, stageNumber, voiceEnabled, speak]);

  async function sendMessage(text?: string) {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;
    const userMsg: Message = { role: "user", content: msg };
    const newHistory = [...history, userMsg];
    setHistory(newHistory);
    setInput("");
    setLoading(true);
    setVoiceState("thinking");

    const userContext = user ? `[Usuario: ${user.name}, nivel: ${user.level}] ` : "";

    try {
      const res = await fetch(`${BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userContext + msg,
          history,
          artwork_title: artworkTitle,
          artwork_artist: artworkArtist,
          stage_title: stageTitle,
          stage_number: stageNumber,
        }),
      });
      const data = await res.json();
      setVoiceState("speaking");
      setHistory([...newHistory, { role: "model", content: data.reply }]);
      if (voiceEnabled && !mutedRef.current) speak(data.reply);
      setTimeout(() => setVoiceState("idle"), 4000);
    } catch {
      setVoiceState("idle");
      setHistory([...newHistory, { role: "model", content: "Problema de conexión. Intenta de nuevo." }]);
    } finally {
      setLoading(false);
    }
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  }

  function toggleVoice() {
    if (voiceEnabled) stop();
    setVoiceEnabled(v => !v);
  }

  function toggleMic() {
    if (listening) stopListening();
    else startListening();
  }

  const statusLabel =
    voiceState === "listening" ? "Escuchando..." :
    voiceState === "thinking"  ? "Analizando..." :
    voiceState === "speaking"  ? "Respondiendo..." :
    user ? `Hola, ${user.name.split(" ")[0]}` : "Tu profesora de arte";

  return (
    <div className="flex flex-col h-full">
      {/* Header — sin avatar */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-pixartek-border shrink-0 bg-gradient-to-r from-pixartek-coral/5 to-transparent">
        {/* Pixi icon — solo emoji de paleta */}
        <div className="w-9 h-9 rounded-full bg-pixartek-coral/15 flex items-center justify-center text-lg shrink-0">
          🎨
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-display font-700 text-sm text-pixartek-ink">Pixi</p>
          <p className={clsx(
            "font-body text-[10px] transition-colors",
            voiceState === "idle" ? "text-pixartek-muted" : "text-pixartek-coral font-600"
          )}>
            {statusLabel}
          </p>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {(!silent || !muted) && (
          <button
            onClick={analyzeCanvas}
            disabled={analyzing || loading}
            title="Ver mi lienzo"
            className="flex items-center gap-1 bg-pixartek-coral text-white text-[10px] font-body font-600 px-2.5 py-1.5 rounded-full disabled:opacity-50 transition hover:opacity-90"
          >
            {analyzing
              ? <span className="w-2.5 h-2.5 border-2 border-white/40 border-t-white rounded-full animate-spin inline-block" />
              : "👁 Ver"}
          </button>
          )}
          <button
            onClick={toggleVoice}
            title={voiceEnabled ? "Silenciar voz" : "Activar voz"}
            className={clsx("w-7 h-7 rounded-full flex items-center justify-center text-xs border-2 transition",
              voiceEnabled ? "border-pixartek-coral bg-pixartek-coral/10 text-pixartek-coral" : "border-pixartek-border text-pixartek-muted")}
          >
            {voiceEnabled ? "🔊" : "🔇"}
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2">
        {silent && history.length === 0 && (
          <div className="flex-1 flex flex-col items-center justify-center gap-4 py-8">
            <div className="w-16 h-16 rounded-full bg-pixartek-coral/10 flex items-center justify-center text-3xl">🎨</div>
            <p className="font-body text-sm text-pixartek-muted text-center px-4">Pixi está lista para ayudarte</p>
            <button
              onClick={triggerGreeting}
              className="px-6 py-3 rounded-2xl bg-pixartek-coral text-white font-display font-700 text-base shadow-btn hover:opacity-90 active:scale-[0.97] transition-all"
            >
              VER
            </button>
          </div>
        )}
        {history.map((msg, i) => (
          <div key={i} className={clsx("flex", msg.role === "user" ? "justify-end" : "justify-start")}>
            {msg.role === "model" && (
              <div className="w-6 h-6 rounded-full bg-pixartek-coral/10 flex items-center justify-center text-xs shrink-0 mr-1.5 mt-0.5">🎨</div>
            )}
            <div className={clsx(
              "max-w-[85%] px-3 py-2 rounded-2xl font-body",
              msg.role === "user"
                ? "bg-pixartek-coral text-white rounded-tr-sm text-xs leading-relaxed"
                : "bg-pixartek-cream text-pixartek-ink rounded-tl-sm"
            )}>
              {msg.role === "model" ? renderMessage(msg.content) : msg.content}
            </div>
          </div>
        ))}

        {(loading || analyzing) && (
          <div className="flex justify-start">
            <div className="w-6 h-6 rounded-full bg-pixartek-coral/10 flex items-center justify-center text-xs shrink-0 mr-1.5 mt-0.5">🎨</div>
            <div className="bg-pixartek-cream rounded-2xl rounded-tl-sm px-3 py-2 flex gap-1 items-center">
              <span className="w-1.5 h-1.5 bg-pixartek-coral/40 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-1.5 h-1.5 bg-pixartek-coral/40 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-1.5 h-1.5 bg-pixartek-coral/40 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-pixartek-border shrink-0">
        <div className="flex gap-2 items-center bg-pixartek-cream rounded-xl px-3 py-1.5">
          <button
            onClick={toggleMic}
            title={listening ? "Detener" : "Hablar con Pixi"}
            className={clsx("w-6 h-6 rounded-full flex items-center justify-center text-xs shrink-0 transition",
              listening ? "bg-red-500 text-white animate-pulse" : "text-pixartek-muted hover:text-pixartek-coral")}
          >
            🎤
          </button>
          <input
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder={listening ? "Escuchando..." : "Pregunta a Pixi..."}
            className="flex-1 bg-transparent text-xs font-body text-pixartek-ink placeholder:text-pixartek-muted outline-none"
          />
          <button onClick={() => sendMessage()} disabled={!input.trim() || loading}
            className="w-6 h-6 rounded-full bg-pixartek-coral flex items-center justify-center disabled:opacity-40 transition hover:opacity-90 shrink-0">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
