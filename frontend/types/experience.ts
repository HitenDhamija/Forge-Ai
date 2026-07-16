export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  priority: string;
  status: string;
  entity_type: string | null;
  entity_id: string | null;
  created_at: string;
  read_at?: string;
  metadata?: Record<string, unknown>;
}

export interface Activity {
  id: string;
  type: string;
  action: string;
  title: string;
  description: string;
  entity_type: string | null;
  entity_id: string | null;
  timestamp: string;
  icon?: string;
  user_id?: string;
}

export interface SearchResult {
  id: string;
  type: string;
  title: string;
  description: string;
  score: number;
  url?: string;
  icon?: string;
  subtitle?: string;
}

export interface SettingDefinition {
  key: string;
  label: string;
  description?: string;
  type: string;
  category: string;
  default: unknown;
  value?: unknown;
  options?: string[];
  required?: boolean;
  group?: string;
}

export interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  order: number;
  completed: boolean;
  skippable: boolean;
}

export interface OnboardingState {
  user_id: string;
  current_step: string | null;
  completed_steps: number;
  total_steps: number;
  is_complete: boolean;
  progress: number;
}

export interface Tutorial {
  id: string;
  title: string;
  description: string;
  difficulty: string;
  estimated_minutes: number;
  steps: number;
}

export interface CommandPaletteItem {
  id: string;
  label: string;
  category: string;
  icon: string;
  shortcut?: string;
  action?: () => void;
}

export interface KeyboardShortcut {
  keys: string[];
  action: string;
}
