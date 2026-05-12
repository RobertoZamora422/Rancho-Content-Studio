import { API_BASE_URL, parseApiResponse } from "./apiClient";
import type { HealthResponse } from "../types/health";

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/health`, { signal });
  return parseApiResponse<HealthResponse>(response);
}
