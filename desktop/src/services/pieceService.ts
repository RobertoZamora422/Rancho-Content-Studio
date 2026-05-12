import { API_BASE_URL, parseApiResponse } from "./apiClient";
import type {
  ContentPiece,
  ContentPieceListResponse,
  ContentPieceUpdate,
  ExportPackageListResponse,
  ExportPackageRequest,
  ExportPackageRunResponse,
  OpenExportFolderResponse,
  PieceGenerationResponse
} from "../types/pieces";

export async function generatePieces(eventId: number): Promise<PieceGenerationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/generate-pieces`, {
    method: "POST"
  });
  return parseApiResponse<PieceGenerationResponse>(response);
}

export async function listContentPieces(eventId: number): Promise<ContentPieceListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/content-pieces`);
  return parseApiResponse<ContentPieceListResponse>(response);
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
  return parseApiResponse<ContentPiece>(response);
}

export async function exportPackage(
  eventId: number,
  payload: ExportPackageRequest
): Promise<ExportPackageRunResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/export-package`, {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "POST"
  });
  return parseApiResponse<ExportPackageRunResponse>(response);
}

export async function listExportPackages(eventId: number): Promise<ExportPackageListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/export-packages`);
  return parseApiResponse<ExportPackageListResponse>(response);
}

export async function openExportPackageFolder(
  eventId: number,
  packageId: number
): Promise<OpenExportFolderResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/events/${eventId}/export-packages/${packageId}/open-folder`,
    {
      method: "POST"
    }
  );
  return parseApiResponse<OpenExportFolderResponse>(response);
}
