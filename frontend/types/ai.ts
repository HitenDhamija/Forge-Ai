export type MessageRole = "system" | "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  model_used: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ModelInfo {
  name: string;
  size: number | null;
  digest: string | null;
  modified_at: string | null;
  parameter_size: string | null;
  quantization: string | null;
}

export type ModelStatusType =
  | "running"
  | "loaded"
  | "available"
  | "offline"
  | "loading";

export interface ModelStatus {
  name: string;
  status: ModelStatusType;
  size: number | null;
  vram_usage: number | null;
}

export interface OllamaStatus {
  connected: boolean;
  version: string | null;
  models_count: number;
  running_models: string[];
}

export interface ChatRequest {
  message: string;
  model?: string;
  conversation_id?: string;
  stream?: boolean;
  temperature?: number;
  max_tokens?: number;
}

export interface ChatResponse {
  conversation_id: string;
  message: ChatMessage;
  model_used: string;
  response_time_ms: number;
  token_count: number | null;
}

export interface ChatStreamChunk {
  conversation_id: string;
  content: string;
  done: boolean;
  model: string;
  created_at: string;
}

export interface ModelListResponse {
  models: ModelInfo[];
  active_model: string;
}

export interface ModelSwitchRequest {
  model_name: string;
}

export interface ModelSwitchResponse {
  previous_model: string;
  current_model: string;
  status: string;
}
