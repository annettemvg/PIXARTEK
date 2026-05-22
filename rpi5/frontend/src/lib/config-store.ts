"use client";
import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface PixartekConfig {
  // Red
  mqttHost: string;
  mqttPort: number;
  rpi5Ip: string;
  rpi4aIp: string;
  rpi4bIp: string;

  // Proyección
  projectionWidth: number;
  projectionHeight: number;
  projectionBrightness: number; // 0–100

  // Audio
  audioEnabled: boolean;
  audioVolume: number; // 0–100

  // Sistema
  kioskMode: boolean;
  language: "es" | "en";
  autoAdvanceStage: boolean;
  autoAdvanceThreshold: number; // precision % needed
}

const DEFAULTS: PixartekConfig = {
  mqttHost: "192.168.86.243",
  mqttPort: 1883,
  rpi5Ip: "192.168.86.243",
  rpi4aIp: "192.168.86.244",
  rpi4bIp: "192.168.86.245",
  projectionWidth: 1920,
  projectionHeight: 1080,
  projectionBrightness: 80,
  audioEnabled: true,
  audioVolume: 70,
  kioskMode: true,
  language: "es",
  autoAdvanceStage: false,
  autoAdvanceThreshold: 90,
};

interface ConfigStore {
  config: PixartekConfig;
  isDirty: boolean;
  set: (patch: Partial<PixartekConfig>) => void;
  save: () => void;
  reset: () => void;
}

export const useConfigStore = create<ConfigStore>()(
  persist(
    (set, get) => ({
      config: DEFAULTS,
      isDirty: false,

      set: (patch) =>
        set(s => ({ config: { ...s.config, ...patch }, isDirty: true })),

      save: () => set({ isDirty: false }),

      reset: () => set({ config: DEFAULTS, isDirty: false }),
    }),
    { name: "pixartek-config" }
  )
);
