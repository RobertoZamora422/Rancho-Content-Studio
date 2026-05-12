export type VisualStylePreset = {
  id: number;
  slug: string;
  name: string;
  description: string | null;
  is_active: boolean;
};

export type VisualStylePresetListResponse = {
  items: VisualStylePreset[];
};
