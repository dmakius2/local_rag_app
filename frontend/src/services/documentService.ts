import { apiClient } from "./apiClient";
import type { DocumentsResponsePayload, DocumentSummary, UploadDocumentsResponsePayload, UploadedDocument } from "@/types";

export async function fetchDocuments(): Promise<DocumentSummary[]> {
  const { data } = await apiClient.get<DocumentsResponsePayload>("/documents");
  return data.documents;
}

export async function uploadDocuments(files: File[]): Promise<UploadedDocument[]> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  const { data } = await apiClient.post<UploadDocumentsResponsePayload>("/documents", formData);
  return data.uploaded.map((d) => ({
    filename: d.filename,
    sizeBytes: d.size_bytes,
    extractable: d.extractable,
  }));
}

export async function deleteDocument(filename: string): Promise<void> {
  await apiClient.delete(`/documents/${encodeURIComponent(filename)}`);
}
