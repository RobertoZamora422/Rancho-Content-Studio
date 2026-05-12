import { API_BASE_URL, parseApiResponse } from "./apiClient";
import type { VisualStylePresetListResponse } from "../types/visualStyles";

export async function listVisualStylePresets(): Promise<VisualStylePresetListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/visual-styles`);
  return parseApiResponse<VisualStylePresetListResponse>(response);
}
