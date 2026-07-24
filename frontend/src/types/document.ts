export interface DocumentSummary {
  filename: string;
  pages: number;
  chunks: number;
}

export interface DocumentsResponsePayload {
  documents: DocumentSummary[];
}

/** Extensions accepted by the upload endpoint (kept in sync with the
 * backend's SUPPORTED_EXTENSIONS in src/document_loader.py). */
export const ACCEPTED_UPLOAD_EXTENSIONS = [".pdf", ".doc", ".docx", ".txt"] as const;

export interface UploadedDocument {
  filename: string;
  sizeBytes: number;
  /** Whether this file type's text is extracted when the index is rebuilt.
   * False for legacy .doc uploads, which are stored but not parsed. */
  extractable: boolean;
}

export interface UploadedDocumentPayload {
  filename: string;
  size_bytes: number;
  extractable: boolean;
}

export interface UploadDocumentsResponsePayload {
  uploaded: UploadedDocumentPayload[];
}
