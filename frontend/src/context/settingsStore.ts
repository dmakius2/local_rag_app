import { create } from "zustand";
import { persist } from "zustand/middleware";
import { DEFAULT_SETTINGS, TOP_K_MAX, TOP_K_MIN, type ChatSettings } from "@/types";

interface SettingsState extends ChatSettings {
  setTopK: (value: number) => void;
  setTemperature: (value: number) => void;
  setModelName: (value: string) => void;
  resetDefaults: () => void;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      ...DEFAULT_SETTINGS,
      setTopK: (value) => set({ topK: clamp(Math.round(value), TOP_K_MIN, TOP_K_MAX) }),
      setTemperature: (value) => set({ temperature: clamp(value, 0, 2) }),
      setModelName: (value) => set({ modelName: value }),
      resetDefaults: () => set(DEFAULT_SETTINGS),
    }),
    { name: "local-rag-settings" }
  )
);
