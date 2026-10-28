export type GenerationMode = 'auto' | 'procedural' | 'ai_text' | 'ai_image';

export interface DimensionsInput {
  width?: number;
  depth?: number;
  height?: number;
  units?: string;
}

export interface MaterialPreferencesInput {
  preset?: string;
  color_hex?: string;
}

export interface GenerationCreateRequest {
  prompt: string;
  generation_mode: GenerationMode;
  reference_image_id?: string;
  object_category?: string;
  style?: string;
  dimensions?: DimensionsInput;
  material_preferences?: MaterialPreferencesInput;
  target_polygon_count?: number;
  export_format?: 'glb' | 'gltf_zip';
  project_id?: string;
}

export interface RefineRequest {
  prompt?: string;
  dimensions?: DimensionsInput;
  material_preferences?: MaterialPreferencesInput;
  style?: string;
  category?: string;
}

export interface GenerationJob {
  id: string;
  owner_id: string;
  project_id?: string;
  generation_mode: string;
  provider: string;
  prompt: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  provider_task_id?: string;
  error_code?: string;
  safe_error_message?: string;
  asset_id?: string;
  asset_download_url?: string;
  validation_report?: any;
  created_at: string;
  completed_at?: string;
}

export interface User {
  id: string;
  email?: string;
  username?: string;
  account_status: string;
  created_at: string;
}

export interface Asset {
  id: string;
  owner_id: string;
  project_id?: string;
  source_job_id?: string;
  prompt?: string;
  generation_mode?: string;
  mime_type: string;
  file_size: number;
  file_checksum: string;
  file_format: string;
  dimensions?: {
    x?: number;
    y?: number;
    z?: number;
  };
  polygon_count: number;
  vertex_count: number;
  validation_status: string;
  validation_report?: any;
  parent_asset_id?: string;
  download_url: string;
  created_at: string;
}

export interface Project {
  id: string;
  owner_id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  asset_count: number;
}

export interface SystemCapabilities {
  blender_available: boolean;
  blender_version?: string;
  supported_procedural_categories: string[];
  ai_provider: string;
  ai_configured: boolean;
  ai_capabilities: {
    name: string;
    text_to_3d: boolean;
    image_to_3d: boolean;
    pricing_summary: string;
  };
  max_upload_size_bytes: number;
  daily_budget_limit_usd: number;
  current_daily_spend_usd: number;
}
