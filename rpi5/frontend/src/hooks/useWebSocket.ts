"use client";
import { useEffect, useRef, useCallback, useState } from "react";

// En producción usa el mismo host que el browser, en SSR fallback a localhost
function getWsUrl() {
  if (typeof window === "undefined") return "ws://localhost:8000";
  return `ws://${window.location.hostname}:8000`;
}
const RECONNECT_DELAY_MS = 3000;

export type WsMessage = {
  topic: string;
  payload: Record<string, unknown>;
};

export type WsStatus = "connecting" | "connected" | "disconnected";

interface Options {
  onMessage: (msg: WsMessage) => void;
  enabled?: boolean;
}

export function useWebSocket({ onMessage, enabled = true }: Options) {
  const wsRef        = useRef<WebSocket | null>(null);
  const timerRef     = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef   = useRef(true);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  const [status, setStatus] = useState<WsStatus>("disconnected");

  const connect = useCallback(() => {
    if (!mountedRef.current || !enabled) return;

    setStatus("connecting");
    const ws = new WebSocket(`${getWsUrl()}/ws`);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) { ws.close(); return; }
      setStatus("connected");
    };

    ws.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data);
        onMessageRef.current(msg);
      } catch { /* malformed message — ignore */ }
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      setStatus("disconnected");
      // Auto-reconnect
      timerRef.current = setTimeout(connect, RECONNECT_DELAY_MS);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [enabled]);

  useEffect(() => {
    mountedRef.current = true;
    if (enabled) connect();
    return () => {
      mountedRef.current = false;
      if (timerRef.current) clearTimeout(timerRef.current);
      wsRef.current?.close();
    };
  }, [connect, enabled]);

  return { status };
}
