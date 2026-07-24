import { create } from "zustand";
import { checkHealth } from "@/services";

export type ApiStatus = "checking" | "online" | "offline";

interface HealthState {
  status: ApiStatus;
  lastCheckedAt: number | null;
  check: () => Promise<void>;
}

export const useHealthStore = create<HealthState>((set) => ({
  status: "checking",
  lastCheckedAt: null,

  check: async () => {
    try {
      const healthy = await checkHealth();
      set({ status: healthy ? "online" : "offline", lastCheckedAt: Date.now() });
    } catch {
      set({ status: "offline", lastCheckedAt: Date.now() });
    }
  },
}));
