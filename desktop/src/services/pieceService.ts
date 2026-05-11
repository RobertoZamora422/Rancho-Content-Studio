import { API_BASE_URL } from "./healthService";
import type {
  ContentPiece,
  ContentPieceListResponse,
  ContentPieceUpdate,
  PieceGenerationResponse
} from "../types/pieces";

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

export async function generatePieces(eventId: number): Promise<PieceGenerationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/generate-pieces`, {
    method: "POST"
  });
  return parseResponse<PieceGenerationResponse>(response);
}

export async function listContentPieces(eventId: number): Promise<ContentPieceListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/content-pieces`);
  return parseResponse<ContentPieceListResponse>(response);
}

export async function updateContentPiece(
  eventId: number,
  pieceId: number,
  payload: ContentPieceUpdate
): Promise<ContentPiece> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/content-pieces/${pieceId}`, {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "PATCH"
  });
  return parseResponse<ContentPiece>(response);
}
