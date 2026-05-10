import { API_BASE_URL } from "./healthService";
import type { AppConfig, AppConfigUpdate, ConfigValidation } from "../types/config";

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`Backend local respondio con estado ${response.status}.`);
  }

  return response.json() as Promise<T>;
}

export async function getConfig(signal?: AbortSignal): Promise<AppConfig> {
  const response = await fetch(`${API_BASE_URL}/api/config`, { signal });
  return parseResponse<AppConfig>(response);
}

export async function updateConfig(payload: AppConfigUpdate): Promise<AppConfig> {
  const response = await fetch(`${API_BASE_URL}/api/config`, {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "PUT"
  });

  return parseResponse<AppConfig>(response);
}

export async function validateTools(): Promise<ConfigValidation> {
  const response = await fetch(`${API_BASE_URL}/api/config/validate-tools`, {
    method: "POST"
  });

  return parseResponse<ConfigValidation>(response);
}
