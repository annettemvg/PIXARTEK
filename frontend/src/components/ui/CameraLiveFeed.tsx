"use client";
import { useState, useEffect } from "react";

export default function CameraLiveFeed() {
  const [frameIndex, setFrameIndex] = useState(0);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    setIsConnected(true);
    // Update frame every 300ms for smooth live feed
    const interval = setInterval(() => {
      setFrameIndex(i => i + 1);
    }, 300);

    return () => clearInterval(interval);
  }, []);

  const timestamp = Date.now();
  const frameUrl = `/api/vision/camera-frame?t=${timestamp}&frame=${frameIndex}`;

  return (
    <div className="w-full bg-black rounded-2xl overflow-hidden border-2 border-pixartek-border shadow-card">
      {/* Camera container */}
      <div className="relative bg-black aspect-video flex items-center justify-center group">

        {/* Live feed image */}
        <img
          key={`frame-${frameIndex}`}
          src={frameUrl}
          alt="Live camera feed - Vision Pi (244)"
          className="w-full h-full object-cover"
          onError={(e) => {
            const img = e.target as HTMLImageElement;
            img.style.display = "none";
          }}
        />

        {/* LIVE indicator badge */}
        <div className="absolute top-3 right-3 flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-red-600 text-white text-xs font-display font-800 shadow-lg z-10">
          <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
          EN VIVO
        </div>

        {/* Camera info overlay */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent px-4 py-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-body text-xs text-white/90 font-semibold">📷 VISIÓN EN VIVO</p>
              <p className="font-body text-xs text-white/60">RPi4-A (244) • Cámara de análisis</p>
            </div>
            <div className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
          </div>
        </div>
      </div>
    </div>
  );
}
