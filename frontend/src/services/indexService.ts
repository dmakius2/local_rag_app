import { apiClient } from "./apiClient";
import type { DeleteIndexResponsePayload, IndexResponsePayload, IndexRebuildResult } from "@/types";

export async function rebuildIndex(): Promise<IndexRebuildResult> {
  const { data } = await apiClient.post<IndexResponsePayload>("/index");
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
