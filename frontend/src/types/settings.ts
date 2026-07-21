export interface ChatSettings {
  /** Caps how many sources are displayed per answer. Functional today: the
   * backend's retrieval top-k is fixed via server-side config (TOP_K env var,
   * see src/config.py); this client-side cap is applied to the sources the
   * API already returns. Once /chat accepts a per-request top_k override,
   * wire it through here without changing this shape. */
  topK: number;
  /** Reserved for a future streaming/creativity control once the backend
   * exposes it. Not wired to any request today. */
  temperature: number;
  /** Reserved for a future multi-model backend. Not wired to any request
   * today — the API always uses the OLLAMA_MODEL configured server-side. */
  modelName: string;
}

export const DEFAULT_SETTINGS: ChatSettings = {
  topK: 5,
  temperature: 0.7,
  modelName: "llama3.2",
};

export const TOP_K_MIN = 1;
export const TOP_K_MAX = 20;
