import { API_BASE_URL } from "./healthService";
import type {
  LibraryCopyListResponse,
  LibraryMediaListResponse,
  LibraryPieceListResponse,
  LibraryQuery,
  LibrarySearchResponse
} from "../types/library";

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

export async function listLibraryMedia(query: LibraryQuery): Promise<LibraryMediaListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/library/media${buildQuery(query)}`);
  return parseResponse<LibraryMediaListResponse>(response);
}

export async function listLibraryPieces(query: LibraryQuery): Promise<LibraryPieceListResponse> {
  const { file_type, ...rest } = query;
  const response = await fetch(
    `${API_BASE_URL}/api/library/pieces${buildQuery({ ...rest, piece_type: query.piece_type ?? file_type })}`
  );
  return parseResponse<LibraryPieceListResponse>(response);
}

export async function listLibraryCopies(query: LibraryQuery): Promise<LibraryCopyListResponse> {
  const { file_type, ...rest } = query;
  const response = await fetch(
    `${API_BASE_URL}/api/library/copies${buildQuery({ ...rest, copy_type: query.copy_type ?? file_type })}`
  );
  return parseResponse<LibraryCopyListResponse>(response);
}

export async function searchLibrary(query: LibraryQuery): Promise<LibrarySearchResponse> {
  const response = await fetch(`${API_BASE_URL}/api/library/search${buildQuery(query)}`);
  return parseResponse<LibrarySearchResponse>(response);
}

function buildQuery(query: LibraryQuery) {
  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== null && `${value}`.trim() !== "") {
      params.set(key, `${value}`);
    }
  });
  const serialized = params.toString();
  return serialized ? `?${serialized}` : "";
}
