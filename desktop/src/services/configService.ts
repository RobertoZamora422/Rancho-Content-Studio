import { API_BASE_URL, parseApiResponse } from "./apiClient";
import type { AppConfig, AppConfigUpdate, ConfigValidation } from "../types/config";

export async function getConfig(signal?: AbortSignal): Promise<AppConfig> {
  const response = await fetch(`${API_BASE_URL}/api/config`, { signal });
  return parseApiResponse<AppConfig>(response);
}

export async function updateConfig(payload: AppConfigUpdate): Promise<AppConfig> {
  const response = await fetch(`${API_BASE_URL}/api/config`, {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "PUT"
  });

  return parseApiResponse<AppConfig>(response);
}

export async function validateTools(): Promise<ConfigValidation> {
  const response = await fetch(`${API_BASE_URL}/api/config/validate-tools`, {
    method: "POST"
  });

  return parseApiResponse<ConfigValidation>(response);
}
