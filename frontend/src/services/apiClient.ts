import axios, { AxiosError } from "axios";
import { ApiError, type ErrorResponsePayload } from "@/types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 60_000,
  headers: { "Content-Type": "application/json" },
});

/** Every request/response error is normalized to an ApiError so components
 * only ever branch on `error.kind`, never on axios/HTTP internals. */
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ErrorResponsePayload>) => {
    if (error.code === "ECONNABORTED") {
      return Promise.reject(
        new ApiError("The request took too long to respond. The model may still be generating — try again.", "timeout")
      );
    }

    if (!error.response) {
      return Promise.reject(
        new ApiError(
          `Can't reach the Local RAG API at ${BASE_URL}. Make sure the backend is running.`,
          "network"
        )
      );
    }

    const status = error.response.status;
    const detail = error.response.data?.detail;

    if (status === 404) {
      return Promise.reject(new ApiError(detail ?? "Not found.", "not_found", status));
    }
    if (status === 422) {
      return Promise.reject(new ApiError(detail ?? "Invalid request.", "validation", status));
    }
    if (status === 503) {
      return Promise.reject(
        new ApiError(detail ?? "The language model backend (Ollama) is unavailable.", "server", status)
      );
    }
    if (status >= 500) {
      return Promise.reject(new ApiError(detail ?? "The server encountered an error.", "server", status));
    }
    if (status >= 400) {
      return Promise.reject(new ApiError(detail ?? "The request was rejected.", "validation", status));
    }

    return Promise.reject(new ApiError(detail ?? "Something went wrong.", "unknown", status));
  }
);
