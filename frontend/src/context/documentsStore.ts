import { create } from "zustand";
import { deleteDocument as deleteDocumentRequest, fetchDocuments, uploadDocuments } from "@/services";
import { ACCEPTED_UPLOAD_EXTENSIONS, ApiError, type DocumentSummary, type UploadedDocument } from "@/types";

function hasAcceptedExtension(filename: string): boolean {
  const lower = filename.toLowerCase();
  return ACCEPTED_UPLOAD_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

interface DocumentsState {
  documents: DocumentSummary[];
  isLoading: boolean;
  error: string | null;
  hasLoaded: boolean;
  loadDocuments: () => Promise<void>;

  isUploading: boolean;
  uploadError: string | null;
  lastUpload: UploadedDocument[] | null;
  uploadFiles: (files: File[]) => Promise<void>;
  dismissUploadResult: () => void;

  deletingFilenames: Set<string>;
  deleteError: string | null;
  deleteDocument: (filename: string) => Promise<void>;
  dismissDeleteError: () => void;
}

export const useDocumentsStore = create<DocumentsState>((set, get) => ({
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

  isUploading: false,
  uploadError: null,
  lastUpload: null,

  uploadFiles: async (files: File[]) => {
    if (get().isUploading || files.length === 0) return;

    const rejected = files.filter((f) => !hasAcceptedExtension(f.name));
    if (rejected.length > 0) {
      set({
        uploadError: `Unsupported file type: ${rejected.map((f) => f.name).join(", ")}. Allowed: ${ACCEPTED_UPLOAD_EXTENSIONS.join(", ")}`,
        lastUpload: null,
      });
      return;
    }

    set({ isUploading: true, uploadError: null, lastUpload: null });
    try {
      const uploaded = await uploadDocuments(files);
      set({ isUploading: false, lastUpload: uploaded });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Upload failed.";
      set({ isUploading: false, uploadError: message });
    }
  },

  dismissUploadResult: () => set({ lastUpload: null, uploadError: null }),

  deletingFilenames: new Set<string>(),
  deleteError: null,

  deleteDocument: async (filename: string) => {
    if (get().deletingFilenames.has(filename)) return;

    set((state) => ({
      deletingFilenames: new Set(state.deletingFilenames).add(filename),
      deleteError: null,
    }));

    try {
      await deleteDocumentRequest(filename);
      set((state) => {
        const deletingFilenames = new Set(state.deletingFilenames);
        deletingFilenames.delete(filename);
        return {
          documents: state.documents.filter((d) => d.filename !== filename),
          deletingFilenames,
        };
      });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Failed to delete document.";
      set((state) => {
        const deletingFilenames = new Set(state.deletingFilenames);
        deletingFilenames.delete(filename);
        return { deletingFilenames, deleteError: message };
      });
    }
  },

  dismissDeleteError: () => set({ deleteError: null }),
}));
