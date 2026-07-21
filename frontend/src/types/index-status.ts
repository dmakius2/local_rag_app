export interface IndexRebuildResult {
  documentsProcessed: number;
  chunksCreated: number;
  elapsedSeconds: number;
}

export interface IndexResponsePayload {
  documents_processed: number;
  chunks_created: number;
  elapsed_seconds: number;
}

export interface DeleteIndexResponsePayload {
  deleted: boolean;
}

export type IndexingPhase = "idle" | "indexing" | "success" | "error";

export interface IndexingState {
  phase: IndexingPhase;
  lastResult: IndexRebuildResult | null;
  error: string | null;
}
