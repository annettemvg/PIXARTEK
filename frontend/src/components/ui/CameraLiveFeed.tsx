"use client";
import { useConfigStore } from "@/lib/config-store";

export default function CameraLiveFeed() {
  const rpi4aIp = useConfigStore(s => s.config.rpi4aIp);
  const feedUrl = `http://${rpi4aIp}:8000/video_feed`;

  return (
    <div className="w-full bg-black rounded-2xl overflow-hidden border-2 border-pixartek-border shadow-card">
      <div className="relative bg-black aspect-video flex items-center justify-center group">

        <img
          src={feedUrl}
          alt="Live camera feed - Vision Pi (244)"
          className="w-full h-full object-cover"
        />

        <div className="absolute top-3 right-3 flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-red-600 text-white text-xs font-display font-800 shadow-lg z-10">
          <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
          EN VIVO
        </div>

        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent px-4 py-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-body text-xs text-white/90 font-semibold">📷 VISIÓN EN VIVO</p>
              <p className="font-body text-xs text-white/60">RPi4-A (244) • Cámara de análisis</p>
            </div>
            <div className="w-2.5 h-2.5 rounded-full bg-green-400 animate-pulse" />
          </div>
        </div>
      </div>
    </div>
  );
}
