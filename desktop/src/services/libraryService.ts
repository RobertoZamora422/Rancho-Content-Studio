import { API_BASE_URL, parseApiResponse } from "./apiClient";
import type {
  LibraryCopyListResponse,
  LibraryMediaListResponse,
  LibraryPieceListResponse,
  LibraryQuery,
  LibrarySearchResponse
} from "../types/library";

export async function listLibraryMedia(query: LibraryQuery): Promise<LibraryMediaListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/library/media${buildQuery(query)}`);
  return parseApiResponse<LibraryMediaListResponse>(response);
}

export async function listLibraryPieces(query: LibraryQuery): Promise<LibraryPieceListResponse> {
  const { file_type, ...rest } = query;
  const response = await fetch(
    `${API_BASE_URL}/api/library/pieces${buildQuery({ ...rest, piece_type: query.piece_type ?? file_type })}`
  );
  return parseApiResponse<LibraryPieceListResponse>(response);
}

export async function listLibraryCopies(query: LibraryQuery): Promise<LibraryCopyListResponse> {
  const { file_type, ...rest } = query;
  const response = await fetch(
    `${API_BASE_URL}/api/library/copies${buildQuery({ ...rest, copy_type: query.copy_type ?? file_type })}`
  );
  return parseApiResponse<LibraryCopyListResponse>(response);
}

export async function searchLibrary(query: LibraryQuery): Promise<LibrarySearchResponse> {
  const response = await fetch(`${API_BASE_URL}/api/library/search${buildQuery(query)}`);
  return parseApiResponse<LibrarySearchResponse>(response);
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
