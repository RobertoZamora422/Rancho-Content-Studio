import { API_BASE_URL, parseApiResponse } from "./apiClient";
import type {
  CopyGenerationRequest,
  CopyGenerationResponse,
  GeneratedCopy,
  GeneratedCopyListResponse,
  GeneratedCopyUpdate
} from "../types/copywriting";

export async function generateCopy(
  eventId: number,
  pieceId: number,
  payload: CopyGenerationRequest = {}
): Promise<CopyGenerationResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/events/${eventId}/content-pieces/${pieceId}/generate-copy`,
    {
      body: JSON.stringify(payload),
      headers: {
        "Content-Type": "application/json"
      },
      method: "POST"
    }
  );
  return parseApiResponse<CopyGenerationResponse>(response);
}

export async function listCopies(
  eventId: number,
  pieceId: number
): Promise<GeneratedCopyListResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/events/${eventId}/content-pieces/${pieceId}/copies`
  );
  return parseApiResponse<GeneratedCopyListResponse>(response);
}

export async function updateCopy(
  eventId: number,
  pieceId: number,
  copyId: number,
  payload: GeneratedCopyUpdate
): Promise<GeneratedCopy> {
  const response = await fetch(
    `${API_BASE_URL}/api/events/${eventId}/content-pieces/${pieceId}/copies/${copyId}`,
    {
      body: JSON.stringify(payload),
      headers: {
        "Content-Type": "application/json"
      },
      method: "PATCH"
    }
  );
  return parseApiResponse<GeneratedCopy>(response);
}
