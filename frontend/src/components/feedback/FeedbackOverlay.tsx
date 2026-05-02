"use client";
import { useState, useEffect } from "react";
import Image from "next/image";

export type FeedbackType = "correcto" | "sugerencia" | "corrección";

interface FeedbackOverlayProps {
  type: FeedbackType;
  visible: boolean;
  onClose: () => void;
  message?: string;
}

export default function FeedbackOverlay({ type, visible, onClose, message }: FeedbackOverlayProps) {
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    if (!visible) return;

    // Play sound
    const audio = new Audio(`/feedback/${type}.wav`);
    audio.play().catch(() => {});
    setPlaying(true);

    // Auto-close after 4 seconds
    const timeout = setTimeout(() => {
      onClose();
    }, 4000);

    return () => clearTimeout(timeout);
  }, [visible, type, onClose]);

  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20">
      {/* Overlay Image */}
      <div className="relative w-full h-full">
        <Image
          src={`/feedback/${type}.png`}
          alt={type}
          fill
          className="object-cover"
          priority
        />

        {/* Close Button (top-right) */}
        <button
          onClick={onClose}
          className="absolute top-8 right-8 z-10 w-16 h-16 rounded-full bg-white/90 shadow-lg flex items-center justify-center text-2xl hover:bg-white transition"
          title="Cerrar"
        >
          ✕
        </button>

        {/* Custom Message (if provided) */}
        {message && (
          <div className="absolute bottom-20 left-1/2 transform -translate-x-1/2 bg-black/70 text-white px-8 py-4 rounded-lg text-center max-w-md">
            <p className="font-body text-lg">{message}</p>
          </div>
        )}
      </div>
    </div>
  );
}
