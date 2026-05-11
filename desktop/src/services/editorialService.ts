import { API_BASE_URL } from "./healthService";
import type { EditorialProfile, EditorialProfileUpdate } from "../types/editorial";

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Backend local respondio con estado ${response.status}.`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        message = payload.detail;
      }
    } catch {
      // Keep the generic HTTP message.
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export async function getDefaultEditorialProfile(): Promise<EditorialProfile> {
  const response = await fetch(`${API_BASE_URL}/api/editorial-profile/default`);
  return parseResponse<EditorialProfile>(response);
}

export async function updateDefaultEditorialProfile(
  payload: EditorialProfileUpdate
): Promise<EditorialProfile> {
  const response = await fetch(`${API_BASE_URL}/api/editorial-profile/default`, {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "PUT"
  });
  return parseResponse<EditorialProfile>(response);
}
