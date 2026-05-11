import { API_BASE_URL } from "./healthService";
import type {
  CopyGenerationRequest,
  CopyGenerationResponse,
  GeneratedCopy,
  GeneratedCopyListResponse,
  GeneratedCopyUpdate
} from "../types/copywriting";

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
  return parseResponse<CopyGenerationResponse>(response);
}

export async function listCopies(
  eventId: number,
  pieceId: number
): Promise<GeneratedCopyListResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/events/${eventId}/content-pieces/${pieceId}/copies`
  );
  return parseResponse<GeneratedCopyListResponse>(response);
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
  return parseResponse<GeneratedCopy>(response);
}
