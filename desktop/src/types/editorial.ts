export type EditorialProfile = {
  id: number;
  brand_id: number;
  name: string;
  tone: string;
  emotional_level: string;
  formality_level: string;
  emoji_style: string;
  description: string | null;
  emoji_policy: string | null;
  hashtags_base: string | null;
  preferred_phrases: string | null;
  words_to_avoid: string | null;
  approved_examples: string | null;
  rejected_examples: string | null;
  copy_rules: string | null;
  is_default: boolean;
  created_at: string;
  updated_at: string;
};

export type EditorialProfileUpdate = {
  name?: string;
  tone?: string;
  emotional_level?: string;
  formality_level?: string;
  emoji_style?: string;
  description?: string | null;
  emoji_policy?: string | null;
  hashtags_base?: string | null;
  preferred_phrases?: string | null;
  words_to_avoid?: string | null;
  approved_examples?: string | null;
  rejected_examples?: string | null;
  copy_rules?: string | null;
};
