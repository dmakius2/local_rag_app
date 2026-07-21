export interface ErrorResponsePayload {
  detail: string;
}

export interface HealthResponsePayload {
  status: string;
}

/** Normalized shape every service function throws/returns on failure, after
 * ApiError classification (see services/apiClient.ts). */
export type ApiErrorKind =
  | "network"
  | "timeout"
  | "server"
  | "not_found"
  | "validation"
  | "unknown";

export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status?: number;

  constructor(message: string, kind: ApiErrorKind, status?: number) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.status = status;
  }
}
