export type MediaSource = {
  id: number;
  event_id: number;
  source_path: string;
  source_type: string;
  status: string;
  file_count: number;
  scanned_at: string | null;
  imported_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type ScanSourceSummary = {
  source_id: number;
  source_path: string;
  supported_files: number;
  unsupported_files: number;
  failed_files: number;
};

export type ScanResponse = {
  job_id: number;
  total_sources: number;
  supported_files: number;
  unsupported_files: number;
  failed_files: number;
  sources: ScanSourceSummary[];
};

export type ImportResponse = {
  job_id: number;
  imported_files: number;
  skipped_files: number;
  failed_files: number;
  total_files: number;
};

export type MetadataProcessResponse = {
  metadata_job_id: number;
  thumbnail_job_id: number;
  total_files: number;
  metadata_updated: number;
  metadata_failed: number;
  thumbnails_generated: number;
  thumbnail_failed: number;
};

export type VisualAnalysisProcessResponse = {
  job_id: number;
  total_photos: number;
  analyzed_photos: number;
  failed_photos: number;
  skipped_non_images: number;
};

export type SimilarityDetectionResponse = {
  job_id: number;
  total_media: number;
  exact_groups: number;
  similar_groups: number;
  grouped_items: number;
  skipped_without_hash: number;
};

export type MediaAnalysis = {
  sharpness_score: number | null;
  brightness_score: number | null;
  contrast_score: number | null;
  noise_score: number | null;
  exposure_score: number | null;
  overall_quality_score: number | null;
  perceptual_hash: string | null;
  analysis_version: string;
  raw_metrics_json: string | null;
  analyzed_at: string;
};

export type OriginalMedia = {
  id: number;
  event_id: number;
  source_id: number | null;
  original_path: string;
  relative_path: string | null;
  filename: string;
  extension: string | null;
  media_type: string;
  mime_type: string | null;
  file_size_bytes: number | null;
  checksum_sha256: string | null;
  capture_datetime: string | null;
  date_source: string | null;
  width: number | null;
  height: number | null;
  duration_seconds: number | null;
  thumbnail_path: string | null;
  thumbnail_url: string | null;
  metadata_json: string | null;
  analysis: MediaAnalysis | null;
  status: string;
  original_exists: boolean;
  imported_at: string;
};

export type OriginalMediaListResponse = {
  items: OriginalMedia[];
};

export type SimilarityGroupItem = {
  id: number;
  group_id: number;
  original_media_id: number;
  distance_score: number | null;
  role: string;
  reason: string | null;
  media: OriginalMedia;
};

export type SimilarityGroup = {
  id: number;
  event_id: number;
  group_type: string;
  representative_media_id: number | null;
  confidence_score: number | null;
  reason: string | null;
  created_at: string;
  items: SimilarityGroupItem[];
};

export type SimilarityGroupListResponse = {
  items: SimilarityGroup[];
};
