import type { EnhancedMedia } from "./importing";

export type PieceGenerationResponse = {
  job_id: number;
  total_available_media: number;
  pieces_created: number;
  pieces_skipped: number;
};

export type ContentPieceMedia = {
  id: number;
  piece_id: number;
  original_media_id: number | null;
  enhanced_media_id: number | null;
  position: number;
  role: string | null;
  notes: string | null;
  enhanced_media: EnhancedMedia | null;
};

export type ContentPiece = {
  id: number;
  event_id: number;
  piece_type: string;
  title: string;
  purpose: string | null;
  target_platform: string | null;
  aspect_ratio: string | null;
  output_path: string | null;
  status: string;
  metadata_json: string | null;
  created_at: string;
  updated_at: string;
  approved_at: string | null;
  rejected_at: string | null;
  media_items: ContentPieceMedia[];
};

export type ContentPieceListResponse = {
  items: ContentPiece[];
};

export type ContentPieceUpdate = {
  title?: string;
  purpose?: string | null;
  target_platform?: string | null;
  aspect_ratio?: string | null;
  status?: string;
  media_item_order?: number[];
};
