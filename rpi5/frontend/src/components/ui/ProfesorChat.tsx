"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import { clsx } from "clsx";

interface Message {
  role: "user" | "model";
  content: string;
}

interface Props {
  artworkTitle?: string;
  artworkArtist?: string;
  stageTitle?: string;
  stageNumber?: number;
  inSession?: boolean; // true cuando está en sesión de pintura activa
}

const BASE = typeof window !== "undefined"
  ? `http://${window.location.hostname}:8000`
  : "http://localhost:8000";

function renderMessage(text: string) {
  const lines = text.split("\n").filter((l, i, arr) => !(l.trim() === "" && arr[i - 1]?.trim() === ""));
  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    const numMatch = line.match(/^\d+\.\s+/);
    if (numMatch) {
      const items: string[] = [];
      while (i < lines.length && lines[i].match(/^\d+\.\s+/)) {
        items.push(lines[i].replace(/^\d+\.\s+/, ""));
        i++;
      }
      elements.push(
        <ol key={`ol-${i}`} className="list-decimal list-outside ml-4 space-y-1 my-1">
          {items.map((item, j) => <li key={j}>{renderInline(item)}</li>)}
        </ol>
      );
      continue;
    }

    if (line.match(/^[-*]\s+/)) {
      const items: string[] = [];
      while (i < lines.length && lines[i].match(/^[-*]\s+/)) {
        items.push(lines[i].replace(/^[-*]\s+/, ""));
        i++;
      }
      elements.push(
        <ul key={`ul-${i}`} className="list-disc list-outside ml-4 space-y-1 my-1">
          {items.map((item, j) => <li key={j}>{renderInline(item)}</li>)}
        </ul>
      );
      continue;
    }

    if (line.trim() === "") { elements.push(<div key={`sp-${i}`} className="h-1" />); i++; continue; }

    elements.push(<p key={`p-${i}`} className="leading-relaxed">{renderInline(line)}</p>);
    i++;
  }

  return <div className="space-y-1 text-sm">{elements}</div>;
}

function renderInline(text: string): React.ReactNode {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith("**") && part.endsWith("**")
      ? <strong key={i} className="font-700">{part.slice(2, -2)}</strong>
      : part
  );
}

const WS_URL = typeof window !== "undefined"
  ? `ws://${window.location.hostname}:8000/ws`
  : "ws://localhost:8000/ws";

export default function PixiChat({ artworkTitle, artworkArtist, stageTitle, stageNumber, inSession }: Props) {
  const [open, setOpen] = useState(false);
  const [history, setHistory] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [autoAnalysis, setAutoAnalysis] = useState(false);
  const [pixiThinking, setPixiThinking] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const autoIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, loading, analyzing, pixiThinking]);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 100);
  }, [open]);

  // WebSocket — recibe feedback automático del monitor
  useEffect(() => {
    if (!inSession) return;
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.topic === "pixi/auto_feedback" && msg.payload?.reply) {
          setPixiThinking(false);
          setHistory(h => [...h, { role: "model", content: msg.payload.reply }]);
          setOpen(true); // Abre el chat automáticamente cuando Pixi tiene algo que decir
        }
        if (msg.topic === "pixi/thinking") {
          setPixiThinking(true);
          setOpen(true);
        }
      } catch {}
    };

    ws.onclose = () => { wsRef.current = null; };

    return () => { ws.close(); };
  }, [inSession]);

  const analyzeCanvas = useCallback(async (silent = false) => {
    if (analyzing || loading) return;
    setAnalyzing(true);
    if (!silent) {
      setHistory(h => [...h, { role: "user", content: "Analiza mi técnica en este momento" }]);
    }
    try {
      const res = await fetch(`${BASE}/api/chat/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          artwork_title: artworkTitle,
          stage_title: stageTitle,
          stage_number: stageNumber,
        }),
      });
      const data = await res.json();
      setHistory(h => [...h, { role: "model", content: data.reply }]);
    } catch {
      setHistory(h => [...h, { role: "model", content: "No pude acceder a la camara en este momento." }]);
    } finally {
      setAnalyzing(false);
    }
  }, [analyzing, loading, artworkTitle, stageTitle, stageNumber]);

  // Auto-análisis cada 30s cuando está activo
  useEffect(() => {
    if (autoAnalysis && inSession) {
      analyzeCanvas(true);
      autoIntervalRef.current = setInterval(() => analyzeCanvas(true), 30000);
    } else {
      if (autoIntervalRef.current) clearInterval(autoIntervalRef.current);
    }
    return () => { if (autoIntervalRef.current) clearInterval(autoIntervalRef.current); };
  }, [autoAnalysis, inSession]);

  async function sendMessage() {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = { role: "user", content: text };
    const newHistory = [...history, userMsg];
    setHistory(newHistory);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          history: history,
          artwork_title: artworkTitle,
          artwork_artist: artworkArtist,
          stage_title: stageTitle,
          stage_number: stageNumber,
        }),
      });
      const data = await res.json();
      setHistory([...newHistory, { role: "model", content: data.reply }]);
    } catch {
      setHistory([...newHistory, { role: "model", content: "Tuve un problema de conexion. Intenta de nuevo." }]);
    } finally {
      setLoading(false);
    }
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  }

  return (
    <>
      {/* Floating button */}
      <button
        onClick={() => setOpen(o => !o)}
        className={clsx(
          "fixed bottom-6 right-6 z-50 w-16 h-16 rounded-full shadow-2xl flex items-center justify-center transition-all duration-300",
          open ? "bg-pixartek-ink scale-95" : "bg-pixartek-coral hover:scale-110"
        )}
        title="Pixi"
      >
        {open ? (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        ) : (
          <span style={{ fontSize: "28px", lineHeight: 1 }}>🎨</span>
        )}
      </button>

      {/* Chat panel */}
      <div className={clsx(
        "fixed bottom-24 right-6 z-50 w-96 max-w-[calc(100vw-2rem)] bg-white rounded-3xl shadow-2xl border border-pixartek-border flex flex-col transition-all duration-300 origin-bottom-right",
        open ? "scale-100 opacity-100" : "scale-90 opacity-0 pointer-events-none"
      )} style={{ height: "540px" }}>

        {/* Header */}
        <div className="bg-pixartek-coral rounded-t-3xl px-5 py-4 flex items-center gap-3 shrink-0">
          <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center text-xl">🎨</div>
          <div>
            <p className="font-display font-700 text-white text-sm">Pixi</p>
            <p className="font-body text-white/80 text-xs">Powered by Gemini 2.5 Flash</p>
          </div>
          {artworkTitle && (
            <div className="ml-auto bg-white/20 rounded-full px-3 py-1">
              <p className="text-white text-xs font-body truncate max-w-24">{artworkTitle}</p>
            </div>
          )}
        </div>

        {/* Vision toolbar — solo en sesión */}
        {inSession && (
          <div className="px-4 py-2.5 border-b border-pixartek-border bg-pixartek-cream/50 flex items-center gap-2 shrink-0">
            <button
              onClick={() => analyzeCanvas(false)}
              disabled={analyzing || loading}
              className="flex items-center gap-1.5 bg-pixartek-coral text-white text-xs font-body font-600 px-3 py-1.5 rounded-full disabled:opacity-50 transition hover:opacity-90"
            >
              {analyzing ? (
                <><span className="w-3 h-3 border-2 border-white/40 border-t-white rounded-full animate-spin inline-block" /> Capturando técnica...</>
              ) : (
                <> Ver mi lienzo</>
              )}
            </button>
            <button
              onClick={() => setAutoAnalysis(a => !a)}
              className={clsx(
                "flex items-center gap-1.5 text-xs font-body font-600 px-3 py-1.5 rounded-full border-2 transition",
                autoAnalysis
                  ? "bg-teal-500 text-white border-teal-500"
                  : "bg-white text-pixartek-muted border-pixartek-border hover:border-pixartek-coral/40"
              )}
            >
              {autoAnalysis ? "Auto ON" : "Auto OFF"}
            </button>
            <span className="text-pixartek-muted text-xs font-body ml-auto">cada 30s</span>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
          {history.length === 0 && (
            <div className="flex-1 flex flex-col items-center justify-center text-center gap-3 py-6">
              <span style={{ fontSize: "48px" }}>🎨</span>
              <p className="font-display font-700 text-pixartek-ink text-base">Hola, soy Pixi</p>
              <p className="font-body text-pixartek-muted text-sm leading-relaxed px-4">
                Tu profesor de arte personal. Preguntame cualquier cosa sobre tecnicas, colores, pinceles o historia del arte.
              </p>
              <div className="flex flex-col gap-2 w-full px-2 mt-1">
                {[
                  "Como mezclo el naranja perfecto?",
                  "Que pincel uso para detalles finos?",
                  "Explicame el impresionismo",
                ].map(q => (
                  <button key={q} onClick={() => { setInput(q); inputRef.current?.focus(); }}
                    className="text-left text-xs font-body text-pixartek-coral border border-pixartek-coral/30 rounded-xl px-3 py-2 hover:bg-pixartek-coral/5 transition">
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {history.map((msg, i) => (
            <div key={i} className={clsx("flex", msg.role === "user" ? "justify-end" : "justify-start")}>
              {msg.role === "model" && (
                <div className="w-7 h-7 rounded-full bg-pixartek-coral/10 flex items-center justify-center text-sm shrink-0 mr-2 mt-1">🎨</div>
              )}
              <div className={clsx(
                "max-w-[82%] px-4 py-3 rounded-2xl font-body",
                msg.role === "user"
                  ? "bg-pixartek-coral text-white rounded-tr-sm text-sm leading-relaxed"
                  : "bg-pixartek-cream text-pixartek-ink rounded-tl-sm"
              )}>
                {msg.role === "model" ? renderMessage(msg.content) : msg.content}
              </div>
            </div>
          ))}

          {(loading || analyzing || pixiThinking) && (
            <div className="flex justify-start">
              <div className="w-7 h-7 rounded-full bg-pixartek-coral/10 flex items-center justify-center text-sm shrink-0 mr-2 mt-1">🎨</div>
              <div className="bg-pixartek-cream rounded-2xl rounded-tl-sm px-4 py-3 flex gap-1 items-center">
                <span className="w-2 h-2 bg-pixartek-coral/40 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}/>
                <span className="w-2 h-2 bg-pixartek-coral/40 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}/>
                <span className="w-2 h-2 bg-pixartek-coral/40 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}/>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-pixartek-border shrink-0">
          <div className="flex gap-2 items-center bg-pixartek-cream rounded-2xl px-4 py-2">
            <input
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Pregunta a Pixi..."
              className="flex-1 bg-transparent text-sm font-body text-pixartek-ink placeholder:text-pixartek-muted outline-none"
            />
            <button onClick={sendMessage} disabled={!input.trim() || loading}
              className="w-8 h-8 rounded-full bg-pixartek-coral flex items-center justify-center disabled:opacity-40 transition hover:opacity-90 shrink-0">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
