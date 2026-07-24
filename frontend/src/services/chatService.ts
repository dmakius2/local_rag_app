import { apiClient } from "./apiClient";
import type { ChatResponsePayload, Source } from "@/types";

export interface ChatResult {
  answer: string;
  sources: Source[];
}

export async function askQuestion(question: string): Promise<ChatResult> {
  console.log("Services: chatService.ts => askQuestion() is running.");

  const { data } = await apiClient.post<ChatResponsePayload>("/chat", { question });
  return {
    answer: data.answer,
    sources: data.sources.map((s) => (
      { document: s.document, page: s.page, chunkText: s.chunk_text }
    )),
  };
}
