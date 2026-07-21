import { apiClient } from "./apiClient";
import type { HealthResponsePayload } from "@/types";

export async function checkHealth(): Promise<boolean> {
  console.log("SERVICES: checkHealth() running");
  const { data } = await apiClient.get<HealthResponsePayload>("/health");
  return data.status === "healthy";
}
