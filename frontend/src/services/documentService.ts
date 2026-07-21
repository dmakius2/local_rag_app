import { apiClient } from "./apiClient";
import type { DocumentsResponsePayload, DocumentSummary } from "@/types";

export async function fetchDocuments(): Promise<DocumentSummary[]> {
  const { data } = await apiClient.get<DocumentsResponsePayload>("/documents");
  return data.documents;
}
