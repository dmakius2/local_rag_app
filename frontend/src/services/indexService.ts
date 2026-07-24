import { apiClient } from "./apiClient";
import type { DeleteIndexResponsePayload, IndexResponsePayload, IndexRebuildResult } from "@/types";

// Rebuilding re-embeds every document from scratch (CPU-bound), which can
// take minutes for large corpora — well past the default request timeout
// that's tuned for chat/upload calls.
const REBUILD_TIMEOUT_MS = 10 * 60_000;

export async function rebuildIndex(): Promise<IndexRebuildResult> {
  const { data } = await apiClient.post<IndexResponsePayload>("/index", undefined, {
    timeout: REBUILD_TIMEOUT_MS,
  });
  return {
    documentsProcessed: data.documents_processed,
    chunksCreated: data.chunks_created,
    elapsedSeconds: data.elapsed_seconds,
  };
}

export async function deleteIndex(): Promise<boolean> {
  const { data } = await apiClient.delete<DeleteIndexResponsePayload>("/index");
  return data.deleted;
}
