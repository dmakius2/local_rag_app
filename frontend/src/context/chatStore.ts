import { create } from "zustand";
import { askQuestion } from "@/services";
import { ApiError, type ChatMessage } from "@/types";

function createId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

interface ChatState {
  messages: ChatMessage[];
  isSending: boolean;
  error: string | null;
  sendMessage: (question: string) => Promise<void>;
  clearHistory: () => void;
  dismissError: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isSending: false,
  error: null, 

  sendMessage: async (question: string) => {
    console.log("Context: chatStore.ts => sendMessage() is running.");
    const trimmed = question.trim();
    if (!trimmed || get().isSending) return;

    const userMessage: ChatMessage = {
      id: createId(),
      role: "user",
      content: trimmed,
      createdAt: Date.now(),
    };

    set((state) => ({
      messages: [...state.messages, userMessage],
      isSending: true,
      error: null,
    }));

    try {
      const result = await askQuestion(trimmed);
      const assistantMessage: ChatMessage = {
        id: createId(),
        role: "assistant",
        content: result.answer,
        sources: result.sources,
        createdAt: Date.now(),
      };
      set((state) => ({ messages: [...state.messages, assistantMessage], isSending: false }));
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
      const assistantMessage: ChatMessage = {
        id: createId(),
        role: "assistant",
        content: message,
        createdAt: Date.now(),
        isError: true,
      };
      set((state) => ({
        messages: [...state.messages, assistantMessage],
        isSending: false,
        error: message,
      }));
    }
  },

  clearHistory: () => set({ messages: [], error: null }),
  dismissError: () => set({ error: null }),
}));
