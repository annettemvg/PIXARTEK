"use client";
import { useState } from "react";
import { useConfigStore } from "@/lib/config-store";

export default function CameraLiveFeed() {
  const rpi4aIp = useConfigStore(s => s.config.rpi4aIp);
  const [connected, setConnected] = useState(false);

  // El navegador maneja el stream MJPEG nativamente con un simple <img>.
  // No se necesita polling, WebSocket ni SSH — la cámara emite como una TV.
  const streamUrl = `http://${rpi4aIp}:8000/video_feed`;

  return (
    <div className="w-full bg-black rounded-2xl overflow-hidden border-2 border-pixartek-border shadow-card">
      <div className="relative bg-black aspect-video flex items-center justify-center">

        {/* Placeholder mientras conecta */}
        {!connected && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-white/40">
            <span className="text-3xl">📷</span>
            <p className="font-body text-xs">Conectando con {rpi4aIp}…</p>
          </div>
        )}

        {/* Stream MJPEG directo — el browser lo consume como si fuera video */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={streamUrl}
          alt="Stream en vivo — Vision Pi (244)"
          className="w-full h-full object-cover"
          onLoad={() => setConnected(true)}
          onError={() => setConnected(false)}
        />

        {/* Badge EN VIVO */}
        <div className="absolute top-3 right-3 flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-red-600 text-white text-xs font-display font-800 shadow-lg z-10">
          <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
          EN VIVO
        </div>

        {/* Info overlay */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent px-4 py-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-body text-xs text-white/90 font-semibold">📷 VISIÓN EN VIVO</p>
              <p className="font-body text-xs text-white/60">RPi4-A ({rpi4aIp}) • puerto 8000</p>
            </div>
            <div className={`w-2.5 h-2.5 rounded-full ${connected ? "bg-green-400 animate-pulse" : "bg-red-400"}`} />
          </div>
        </div>
      </div>
    </div>
  );
}
