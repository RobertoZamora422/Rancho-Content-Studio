import { API_BASE_URL, parseApiResponse } from "./apiClient";
import type { EditorialProfile, EditorialProfileUpdate } from "../types/editorial";

export async function getDefaultEditorialProfile(): Promise<EditorialProfile> {
  const response = await fetch(`${API_BASE_URL}/api/editorial-profile/default`);
  return parseApiResponse<EditorialProfile>(response);
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
  return parseApiResponse<EditorialProfile>(response);
}
