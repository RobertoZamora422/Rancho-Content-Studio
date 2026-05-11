export type GeneratedCopy = {
  id: number;
  piece_id: number;
  editorial_profile_id: number | null;
  copy_type: string;
  variant_label: string | null;
  body: string;
  hashtags_json: string | null;
  cta: string | null;
  style_notes: string | null;
  status: string;
  generation_mode: string;
  ai_provider: string | null;
  prompt_context: string | null;
  user_feedback: string | null;
  output_path: string | null;
  warnings: string[];
  created_at: string;
  updated_at: string;
  approved_at: string | null;
  rejected_at: string | null;
};

export type GeneratedCopyListResponse = {
  items: GeneratedCopy[];
};

export type CopyGenerationResponse = {
  job_id: number;
  piece_id: number;
  copies_created: number;
  feedback: string | null;
  items: GeneratedCopy[];
};

export type CopyGenerationRequest = {
  feedback?: string | null;
};

export type GeneratedCopyUpdate = {
  body?: string;
  status?: string;
  user_feedback?: string | null;
  variant_label?: string | null;
};
