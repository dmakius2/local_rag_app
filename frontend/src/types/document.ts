export interface DocumentSummary {
  filename: string;
  pages: number;
  chunks: number;
}

export interface DocumentsResponsePayload {
  documents: DocumentSummary[];
}
