"use client";
import { useState } from "react";
import CameraLiveFeed from "@/components/ui/CameraLiveFeed";

interface Props {
  isOpen?: boolean;
  onClose?: () => void;
}

export default function VisionAnalysisModal({ isOpen = false, onClose }: Props) {
  const [expanded, setExpanded] = useState(isOpen);

  const handleClose = () => {
    setExpanded(false);
    onClose?.();
  };

  return (
    <>
      {/* Button to open analysis when closed */}
      {!expanded && (
        <button
          onClick={() => setExpanded(true)}
          className="
            w-full py-3 px-4 rounded-xl border-2 border-pixartek-border
            bg-white text-pixartek-ink font-display font-600 text-sm
            hover:border-pixartek-ink/40 hover:bg-pixartek-cream/60
            transition-all duration-150 flex items-center gap-2 justify-center
          "
        >
          📷 Ver Análisis de Visión
        </button>
      )}

      {/* Modal Overlay */}
      {expanded && (
        <div className="fixed inset-0 bg-black/50 z-40 flex items-center justify-center p-4">
          {/* Modal Content */}
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-pixartek-border shrink-0">
              <div>
                <h2 className="font-display font-700 text-xl text-pixartek-ink">
                  📷 Análisis de Visión
                </h2>
                <p className="font-body text-xs text-pixartek-muted mt-1">
                  Ver lo que observa la cámara del lienzo
                </p>
              </div>
              <button
                onClick={handleClose}
                className="
                  w-9 h-9 flex items-center justify-center rounded-full
                  bg-pixartek-cream text-pixartek-ink font-display font-700 text-lg
                  hover:bg-pixartek-coral hover:text-white transition-all duration-150
                "
                title="Cerrar"
              >
                ✕
              </button>
            </div>

            {/* Camera Feed */}
            <div className="flex-1 p-6 overflow-auto flex flex-col items-center justify-center">
              <div className="w-full max-w-xl">
                <CameraLiveFeed />
              </div>

              {/* Info below camera */}
              <div className="mt-6 text-center">
                <p className="font-body text-sm text-pixartek-muted mb-2">
                  Stream en vivo de RPi4-A (244)
                </p>
                <p className="font-body text-xs text-pixartek-muted/60">
                  Actualiza cada 300ms • Alineación de lienzo visible
                </p>
              </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-pixartek-border bg-pixartek-cream shrink-0">
              <button
                onClick={handleClose}
                className="
                  w-full py-3 rounded-xl font-display font-700 text-lg text-white
                  bg-pixartek-coral shadow-btn
                  hover:opacity-90 active:scale-[0.99] transition-all duration-150
                "
              >
                Cerrar ✕
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
