export type RequestStatus = "QUEUED" | "RUNNING" | "DONE" | "FAILED";
export type ViewerPlan = "free" | "premium";

export interface ReferenceOption {
  id: number;
  name: string;
  code: string;
}

export interface BootstrapPayload {
  app_name: string;
  default_model: string;
  reference_data: {
    seasons: ReferenceOption[];
    occasions: ReferenceOption[];
    styles: ReferenceOption[];
  };
}

export interface RequestStatusPayload {
  id: string;
  status: RequestStatus;
  error_message: string;
  image_error_message: string;
  ai_latency_ms: number | null;
  image_latency_ms: number | null;
  created_at: string;
  updated_at: string;
  detail_url: string;
}

export interface DetectedItem {
  id: string;
  label: string;
  category: string;
  colors: string[];
  pattern: string | null;
  material: string | null;
  confidence: number;
  notes: string | null;
}

export interface OutfitUsageItem {
  detected_item_id: string;
  role: string;
}

export interface OutfitCard {
  key: string;
  option_label: string;
  variant_label: string;
  is_generated_source: boolean;
  title: string;
  why_it_works: string;
  fit_notes: string;
  color_notes: string;
  items: OutfitUsageItem[];
}

export interface ToBuyItem {
  name: string;
  why_needed: string;
  google_query: string;
  priority: string;
  google_search_url: string;
}

export interface AdviceBlock {
  style: string[];
  care: string[];
  impression: string[];
}

export interface GeneratedOutfitMeta {
  key: string;
  option_label: string;
  variant_label: string;
  title: string;
}

export interface RequestResultPayload {
  detected_items: DetectedItem[];
  outfits: {
    safe: unknown;
    bold: unknown;
    creative: unknown;
  };
  to_buy: Array<{
    name: string;
    why_needed: string;
    google_query: string;
    priority: string;
  }>;
  advice: AdviceBlock;
  generated_outfit: GeneratedOutfitMeta | null;
  outfit_cards: OutfitCard[];
  to_buy_with_links: ToBuyItem[];
}

export interface RequestDetailPayload extends RequestStatusPayload {
  season: ReferenceOption;
  occasion: ReferenceOption;
  style: ReferenceOption;
  additional_info: string;
  ai_model: string;
  image_model: string;
  generated_image_url: string | null;
  image_original_url: string | null;
  result: RequestResultPayload | null;
}

export interface CreateRequestResponse extends RequestStatusPayload {}
