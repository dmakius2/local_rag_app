export interface Source {
  document: string;
  page: number;
  chunkText: string;
}

export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  sources?: Source[];
  createdAt: number;
  isError?: boolean;
}

export interface ChatRequestPayload {
  question: string;
}

export interface ChatResponsePayload {
  answer: string;
  sources: Array<{ document: string; page: number; chunk_text: string }>;
}
