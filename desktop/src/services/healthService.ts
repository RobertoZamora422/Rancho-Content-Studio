import type { HealthResponse } from "../types/health";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8010";

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/health`, { signal });

  if (!response.ok) {
    throw new Error(`Backend local respondio con estado ${response.status}.`);
  }

  return response.json() as Promise<HealthResponse>;
}
