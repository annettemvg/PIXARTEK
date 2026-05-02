"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { clsx } from "clsx";
import { useConfigStore } from "@/lib/config-store";
import SettingsRow from "@/components/ui/SettingsRow";
import { checkHealth } from "@/lib/api-client";

type Tab = "red" | "proyeccion" | "audio" | "sistema";

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: "red",        label: "Red",         icon: "🌐" },
  { id: "proyeccion", label: "Proyección",  icon: "📽" },
  { id: "audio",      label: "Audio",       icon: "🔊" },
  { id: "sistema",    label: "Sistema",     icon: "⚙️" },
];

export default function SettingsPage() {
  const router = useRouter();
  const { config, isDirty, set, save, reset } = useConfigStore();
  const [activeTab, setActiveTab] = useState<Tab>("red");
  const [pingResult, setPingResult] = useState<"idle" | "ok" | "error">("idle");
  const [pinging, setPinging] = useState(false);
  const [saved, setSaved] = useState(false);

  async function handlePing() {
    setPinging(true);
    setPingResult("idle");
    const ok = await checkHealth();
    setPingResult(ok ? "ok" : "error");
    setPinging(false);
  }

  function handleSave() {
    save();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div className="flex h-screen bg-pixartek-primary overflow-hidden">

      {/* Sidebar */}
      <div className="w-56 border-r border-white/10 flex flex-col bg-pixartek-ink shrink-0">
        <div className="p-5 border-b border-white/10">
          <button
            onClick={() => router.push("/")}
            className="text-gray-400 hover:text-white text-sm transition"
          >
            ← Inicio
          </button>
          <h1 className="text-xl font-bold mt-3">Configuración</h1>
        </div>

        <nav className="flex flex-col p-3 gap-1">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                "flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-left transition",
                activeTab === tab.id
                  ? "bg-pixartek-accent/20 text-pixartek-accent"
                  : "text-gray-400 hover:bg-white/5 hover:text-white"
              )}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>

        <div className="mt-auto p-4 border-t border-white/10 flex flex-col gap-2">
          <button
            onClick={handleSave}
            className={clsx(
              "w-full py-2.5 rounded-xl text-sm font-semibold transition",
              saved
                ? "bg-emerald-500 text-white"
                : isDirty
                  ? "bg-pixartek-accent hover:opacity-90 text-white"
                  : "bg-white/10 text-gray-400 cursor-not-allowed"
            )}
            disabled={!isDirty && !saved}
          >
            {saved ? "✓ Guardado" : "Guardar cambios"}
          </button>
          <button
            onClick={reset}
            className="w-full py-2 rounded-xl text-xs text-gray-500 hover:text-gray-300 hover:bg-white/5 transition"
          >
            Restablecer defaults
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-xl">

          {/* ── RED ── */}
          {activeTab === "red" && (
            <section>
              <h2 className="text-lg font-bold mb-1">Red y Conectividad</h2>
              <p className="text-sm text-gray-400 mb-6">IPs de los nodos Raspberry Pi en la red local (192.168.1.x)</p>

              <div className="bg-pixartek-ink rounded-2xl p-5 mb-4">
                <p className="text-xs text-gray-400 uppercase tracking-wide mb-3">MQTT Broker</p>
                <SettingsRow label="Host / IP"        type="text"   value={config.mqttHost}  onChange={v => set({ mqttHost: v })} placeholder="192.168.1.10" />
                <SettingsRow label="Puerto"           type="number" value={config.mqttPort}  onChange={v => set({ mqttPort: Number(v) })} min={1} max={65535} />
              </div>

              <div className="bg-pixartek-ink rounded-2xl p-5 mb-4">
                <p className="text-xs text-gray-400 uppercase tracking-wide mb-3">Nodos</p>
                <SettingsRow label="RPi5 — Principal"  description="Orquestador + UI + DB" type="text" value={config.rpi5Ip}  onChange={v => set({ rpi5Ip: v })} />
                <SettingsRow label="RPi4-A — Proyección" description="Proyector HDMI"      type="text" value={config.rpi4aIp} onChange={v => set({ rpi4aIp: v })} />
                <SettingsRow label="RPi4-B — Visión"   description="Cámara HD + OpenCV"    type="text" value={config.rpi4bIp} onChange={v => set({ rpi4bIp: v })} />
              </div>

              {/* Ping test */}
              <div className="bg-pixartek-ink rounded-2xl p-5">
                <p className="text-xs text-gray-400 uppercase tracking-wide mb-3">Prueba de conexión</p>
                <div className="flex items-center gap-3">
                  <button
                    onClick={handlePing}
                    disabled={pinging}
                    className="px-5 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm transition disabled:opacity-50"
                  >
                    {pinging ? "Probando..." : "Ping al backend"}
                  </button>
                  {pingResult === "ok"    && <span className="text-emerald-400 text-sm">✓ Conectado</span>}
                  {pingResult === "error" && <span className="text-rose-400 text-sm">✗ Sin respuesta</span>}
                </div>
              </div>
            </section>
          )}

          {/* ── PROYECCIÓN ── */}
          {activeTab === "proyeccion" && (
            <section>
              <h2 className="text-lg font-bold mb-1">Proyección</h2>
              <p className="text-sm text-gray-400 mb-6">Configuración del proyector conectado a RPi4-A</p>

              <div className="bg-pixartek-ink rounded-2xl p-5">
                <SettingsRow label="Resolución ancho"  type="number" value={config.projectionWidth}      onChange={v => set({ projectionWidth: Number(v) })}  min={640} max={3840} />
                <SettingsRow label="Resolución alto"   type="number" value={config.projectionHeight}     onChange={v => set({ projectionHeight: Number(v) })} min={480} max={2160} />
                <SettingsRow label="Brillo"            type="slider" value={config.projectionBrightness} onChange={v => set({ projectionBrightness: v })}     min={0}   max={100} unit="%" />
              </div>

              <div className="mt-4 bg-pixartek-ink rounded-2xl p-5">
                <p className="text-xs text-gray-400 uppercase tracking-wide mb-3">Resoluciones comunes</p>
                <div className="flex gap-2 flex-wrap">
                  {[["1280×720", 1280, 720], ["1920×1080", 1920, 1080], ["1280×800", 1280, 800]].map(([label, w, h]) => (
                    <button
                      key={label as string}
                      onClick={() => set({ projectionWidth: w as number, projectionHeight: h as number })}
                      className="px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-xs transition"
                    >
                      {label as string}
                    </button>
                  ))}
                </div>
              </div>
            </section>
          )}

          {/* ── AUDIO ── */}
          {activeTab === "audio" && (
            <section>
              <h2 className="text-lg font-bold mb-1">Audio</h2>
              <p className="text-sm text-gray-400 mb-6">Feedback auditivo durante la sesión de pintura</p>

              <div className="bg-pixartek-ink rounded-2xl p-5">
                <SettingsRow label="Audio habilitado" type="toggle" value={config.audioEnabled} onChange={v => set({ audioEnabled: v })} />
                <SettingsRow label="Volumen"           type="slider" value={config.audioVolume}   onChange={v => set({ audioVolume: v })} min={0} max={100} unit="%" description="Volumen del feedback de voz" />
              </div>
            </section>
          )}

          {/* ── SISTEMA ── */}
          {activeTab === "sistema" && (
            <section>
              <h2 className="text-lg font-bold mb-1">Sistema</h2>
              <p className="text-sm text-gray-400 mb-6">Comportamiento general del kiosk</p>

              <div className="bg-pixartek-ink rounded-2xl p-5 mb-4">
                <SettingsRow
                  label="Modo kiosk"
                  description="Oculta la barra del sistema al desplegar en RPi"
                  type="toggle"
                  value={config.kioskMode}
                  onChange={v => set({ kioskMode: v })}
                />
                <SettingsRow
                  label="Idioma"
                  type="select"
                  value={config.language}
                  onChange={v => set({ language: v as "es" | "en" })}
                  options={[{ value: "es", label: "Español" }, { value: "en", label: "English" }]}
                />
              </div>

              <div className="bg-pixartek-ink rounded-2xl p-5 mb-4">
                <p className="text-xs text-gray-400 uppercase tracking-wide mb-3">Avance automático</p>
                <SettingsRow
                  label="Auto-avanzar etapa"
                  description="Pasa a la siguiente etapa al alcanzar el umbral de precisión"
                  type="toggle"
                  value={config.autoAdvanceStage}
                  onChange={v => set({ autoAdvanceStage: v })}
                />
                <SettingsRow
                  label="Umbral de precisión"
                  type="slider"
                  value={config.autoAdvanceThreshold}
                  onChange={v => set({ autoAdvanceThreshold: v })}
                  min={50}
                  max={100}
                  unit="%"
                />
              </div>

              <div className="bg-pixartek-ink rounded-2xl p-5">
                <p className="text-xs text-gray-400 uppercase tracking-wide mb-3">Acerca de</p>
                <div className="flex flex-col gap-2 text-sm text-gray-400">
                  <div className="flex justify-between"><span>Versión</span><span className="text-white">0.1.0</span></div>
                  <div className="flex justify-between"><span>Plataforma</span><span className="text-white">3× Raspberry Pi</span></div>
                  <div className="flex justify-between"><span>Stack</span><span className="text-white">Next.js · FastAPI · MQTT</span></div>
                </div>
              </div>
            </section>
          )}

        </div>
      </div>
    </div>
  );
}
