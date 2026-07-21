import { create } from "zustand";
import { fetchDocuments } from "@/services";
import { ApiError, type DocumentSummary } from "@/types";

interface DocumentsState {
  documents: DocumentSummary[];
  isLoading: boolean;
  error: string | null;
  hasLoaded: boolean;
  loadDocuments: () => Promise<void>;
}

export const useDocumentsStore = create<DocumentsState>((set) => ({
  documents: [],
  isLoading: false,
  error: null,
  hasLoaded: false,

  loadDocuments: async () => {
    set({ isLoading: true, error: null });
    try {
      const documents = await fetchDocuments();
      set({ documents, isLoading: false, hasLoaded: true });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Failed to load documents.";
      set({ isLoading: false, error: message, hasLoaded: true });
    }
  },
}));
