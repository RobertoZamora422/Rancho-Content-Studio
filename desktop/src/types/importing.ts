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

export type CurationProcessResponse = {
  job_id: number;
  total_media: number;
  selected: number;
  alternative: number;
  rejected: number;
  manual_review: number;
  preserved_manual_overrides: number;
};

export type PhotoEnhancementRequest = {
  preset_slug: string;
};

export type PhotoEnhancementResponse = {
  job_id: number;
  total_selected: number;
  enhanced: number;
  skipped: number;
  failed: number;
  preset_slug: string;
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

export type CuratedMedia = {
  id: number;
  event_id: number;
  original_media_id: number;
  selection_status: string;
  reason: string | null;
  score: number | null;
  selected_by: string;
  is_manual_override: boolean;
  created_at: string;
  updated_at: string;
  media: OriginalMedia;
};

export type CuratedMediaListResponse = {
  items: CuratedMedia[];
};

export type CuratedMediaUpdate = {
  selection_status: string;
  reason?: string | null;
};

export type EnhancedMedia = {
  id: number;
  event_id: number;
  original_media_id: number;
  curated_media_id: number | null;
  output_path: string;
  output_url: string;
  enhancement_type: string;
  preset_slug: string | null;
  status: string;
  width: number | null;
  height: number | null;
  duration_seconds: number | null;
  notes: string | null;
  created_at: string;
  approved_at: string | null;
  rejected_at: string | null;
  media: OriginalMedia;
};

export type EnhancedMediaListResponse = {
  items: EnhancedMedia[];
};

export type EnhancedMediaUpdate = {
  status: string;
  reason?: string | null;
};
