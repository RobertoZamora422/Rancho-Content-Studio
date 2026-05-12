import { API_BASE_URL, parseApiResponse } from "./apiClient";
import type {
  CuratedMedia,
  CuratedMediaListResponse,
  CuratedMediaUpdate,
  CurationProcessResponse,
  EnhancedMedia,
  EnhancedMediaListResponse,
  EnhancedMediaUpdate,
  ImportResponse,
  MediaSource,
  MetadataProcessResponse,
  OriginalMediaListResponse,
  PhotoEnhancementResponse,
  ScanResponse,
  SimilarityDetectionResponse,
  SimilarityGroupListResponse,
  VideoEnhancementRequest,
  VideoEnhancementResponse,
  VisualAnalysisProcessResponse
} from "../types/importing";
import type { JobListResponse } from "../types/jobs";

export async function listSources(eventId: number): Promise<MediaSource[]> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/sources`);
  return parseApiResponse<MediaSource[]>(response);
}

export async function addSource(eventId: number, sourcePath: string): Promise<MediaSource> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/sources`, {
    body: JSON.stringify({ source_path: sourcePath }),
    headers: {
      "Content-Type": "application/json"
    },
    method: "POST"
  });
  return parseApiResponse<MediaSource>(response);
}

export async function scanSources(eventId: number): Promise<ScanResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/scan`, {
    method: "POST"
  });
  return parseApiResponse<ScanResponse>(response);
}

export async function importMedia(eventId: number): Promise<ImportResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/import`, {
    method: "POST"
  });
  return parseApiResponse<ImportResponse>(response);
}

export async function processMetadataAndThumbnails(
  eventId: number
): Promise<MetadataProcessResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/process-metadata`, {
    method: "POST"
  });
  return parseApiResponse<MetadataProcessResponse>(response);
}

export async function analyzePhotos(eventId: number): Promise<VisualAnalysisProcessResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/analyze-photos`, {
    method: "POST"
  });
  return parseApiResponse<VisualAnalysisProcessResponse>(response);
}

export async function detectSimilarity(eventId: number): Promise<SimilarityDetectionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/detect-similarity`, {
    method: "POST"
  });
  return parseApiResponse<SimilarityDetectionResponse>(response);
}

export async function curateMedia(eventId: number): Promise<CurationProcessResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/curate-media`, {
    method: "POST"
  });
  return parseApiResponse<CurationProcessResponse>(response);
}

export async function enhancePhotos(
  eventId: number,
  presetSlug: string
): Promise<PhotoEnhancementResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/enhance-photos`, {
    body: JSON.stringify({ preset_slug: presetSlug }),
    headers: {
      "Content-Type": "application/json"
    },
    method: "POST"
  });
  return parseApiResponse<PhotoEnhancementResponse>(response);
}

export async function enhanceVideos(
  eventId: number,
  payload: VideoEnhancementRequest
): Promise<VideoEnhancementResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/enhance-videos`, {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "POST"
  });
  return parseApiResponse<VideoEnhancementResponse>(response);
}

export async function listOriginalMedia(eventId: number): Promise<OriginalMediaListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/media/original`);
  return parseApiResponse<OriginalMediaListResponse>(response);
}

export async function listSimilarityGroups(eventId: number): Promise<SimilarityGroupListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/similarity-groups`);
  return parseApiResponse<SimilarityGroupListResponse>(response);
}

export async function listCuratedMedia(eventId: number): Promise<CuratedMediaListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/curated-media`);
  return parseApiResponse<CuratedMediaListResponse>(response);
}

export async function updateCuratedMedia(
  eventId: number,
  curatedId: number,
  payload: CuratedMediaUpdate
): Promise<CuratedMedia> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/curated-media/${curatedId}`, {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "PATCH"
  });
  return parseApiResponse<CuratedMedia>(response);
}

export async function listEnhancedMedia(eventId: number): Promise<EnhancedMediaListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/enhanced-media`);
  return parseApiResponse<EnhancedMediaListResponse>(response);
}

export async function updateEnhancedMedia(
  eventId: number,
  enhancedId: number,
  payload: EnhancedMediaUpdate
): Promise<EnhancedMedia> {
  const response = await fetch(
    `${API_BASE_URL}/api/events/${eventId}/enhanced-media/${enhancedId}`,
    {
      body: JSON.stringify(payload),
      headers: {
        "Content-Type": "application/json"
      },
      method: "PATCH"
    }
  );
  return parseApiResponse<EnhancedMedia>(response);
}

export async function listEventJobs(eventId: number): Promise<JobListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/jobs`);
  return parseApiResponse<JobListResponse>(response);
}
