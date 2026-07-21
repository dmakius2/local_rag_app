import { create } from "zustand";
import { rebuildIndex } from "@/services";
import { useDocumentsStore } from "@/context/documentsStore";
import { ApiError, type IndexingPhase, type IndexRebuildResult } from "@/types";

interface IndexState {
  phase: IndexingPhase;
  lastResult: IndexRebuildResult | null;
  error: string | null;
  triggerReindex: () => Promise<void>;
  dismiss: () => void;
}

export const useIndexStore = create<IndexState>((set) => ({
  phase: "idle",
  lastResult: null,
  error: null,

  triggerReindex: async () => {
    set({ phase: "indexing", error: null });
    try {
      const result = await rebuildIndex();
      set({ phase: "success", lastResult: result });
      await useDocumentsStore.getState().loadDocuments();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Reindexing failed.";
      set({ phase: "error", error: message });
    }
  },

  dismiss: () => set({ phase: "idle", error: null }),
}));
