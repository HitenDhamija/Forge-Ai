export const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || "ForgeAI";
export const APP_VERSION = process.env.NEXT_PUBLIC_APP_VERSION || "0.1.0";
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export const STORAGE_KEYS = {
  AUTH_TOKEN: "forge-auth-token",
  REFRESH_TOKEN: "forge-refresh-token",
  THEME: "forge-theme",
  SIDEBAR_STATE: "forge-sidebar-state",
} as const;

export const ROUTES = {
  HOME: "/",
  LOGIN: "/login",
  REGISTER: "/register",
  DASHBOARD: "/dashboard",
  PROJECTS: "/projects",
  PROFILE: "/profile",
  SETTINGS: "/settings",
  DOCUMENTATION: "/documentation",
  FUTURE_AI: "/future-ai",
  FUTURE_AGENTS: "/future-agents",
} as const;

export const BREAKPOINTS = {
  SM: 640,
  MD: 768,
  LG: 1024,
  XL: 1280,
  "2XL": 1536,
} as const;

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: "/auth/login",
    REGISTER: "/auth/register",
    REFRESH: "/auth/refresh",
    LOGOUT: "/auth/logout",
  },
  USERS: {
    ME: "/users/me",
    UPDATE: "/users/me",
  },
  PROJECTS: {
    LIST: "/projects",
    CREATE: "/projects",
    GET: (id: string) => `/projects/${id}`,
    UPDATE: (id: string) => `/projects/${id}`,
    DELETE: (id: string) => `/projects/${id}`,
  },
} as const;

export const AI_ROUTES = {
  WORKSPACE: "/ai",
  CHAT: "/ai/chat",
} as const;

export const AI_ENDPOINTS = {
  CHAT: "/ai/chat",
  CHAT_STREAM: "/ai/chat/stream",
  MODELS: "/ai/models",
  MODEL_SWITCH: "/ai/models/switch",
  STATUS: "/ai/status",
  STOP: "/ai/stop",
  CONVERSATIONS: "/ai/conversations",
} as const;

export const AI_CONFIG = {
  DEFAULT_MODEL: "qwen2.5",
  MAX_PROMPT_LENGTH: 32000,
  MAX_CONTEXT_MESSAGES: 10,
  TYPING_SPEED_MS: 20,
} as const;

export const REPOSITORY_ROUTES = {
  LIST: "/repositories",
  DETAIL: (id: string) => `/repositories/${id}`,
} as const;

export const REPOSITORY_ENDPOINTS = {
  IMPORT: "/repositories/import",
  IMPORT_UPLOAD: "/repositories/import/upload",
  LIST: "/repositories",
  GET: (id: string) => `/repositories/${id}`,
  DELETE: (id: string) => `/repositories/${id}`,
  SUMMARY: (id: string) => `/repositories/${id}/summary`,
  ANALYSIS: (id: string) => `/repositories/${id}/analysis`,
  GRAPH: (id: string) => `/repositories/${id}/graph`,
} as const;

export const MEMORY_ROUTES = {
  WORKSPACE: "/memory",
} as const;

export const MEMORY_ENDPOINTS = {
  INDEX: "/memory/index",
  SEARCH: "/memory/search",
  CONTEXT: "/memory/context",
  REPOSITORIES: "/memory/repositories",
  STATS: "/memory/stats",
  DELETE: (id: string) => `/memory/index/${id}`,
} as const;

export const PLANNER_ROUTES = {
  WORKSPACE: "/planner",
} as const;

export const PLANNER_ENDPOINTS = {
  PLAN: "/planner/plan",
  HISTORY: "/planner/history",
  GET: (id: string) => `/planner/${id}`,
  DELETE: (id: string) => `/planner/${id}`,
} as const;

export const AGENT_ROUTES = {
  WORKSPACE: "/agents",
} as const;

export const AGENT_ENDPOINTS = {
  BASE: "/agents",
  TASKS: "/agents/tasks",
  METRICS: "/agents/metrics/overview",
  GET: (id: string) => `/agents/${id}`,
  TASK: (id: string) => `/agents/tasks/${id}`,
  CANCEL_TASK: (id: string) => `/agents/tasks/${id}/cancel`,
} as const;

export const WORKFLOW_ROUTES = {
  LIST: "/workflows",
  DETAIL: (id: string) => `/workflows/${id}`,
} as const;

export const WORKFLOW_ENDPOINTS = {
  BASE: "/workflows",
  GET: (id: string) => `/workflows/${id}`,
  APPROVE: (id: string) => `/workflows/${id}/approve`,
  START: (id: string) => `/workflows/${id}/start`,
  PAUSE: (id: string) => `/workflows/${id}/pause`,
  RESUME: (id: string) => `/workflows/${id}/resume`,
  CANCEL: (id: string) => `/workflows/${id}/cancel`,
  SUMMARY: (id: string) => `/workflows/${id}/summary`,
} as const;

export const WORKFORCE_ROUTES = {
  DASHBOARD: "/workforce",
} as const;

export const WORKFORCE_ENDPOINTS = {
  BASE: "/workforce",
  STATUS: "/workforce/status",
  EVENTS: "/workforce/events/recent",
  GET: (id: string) => `/workforce/${id}`,
  ROLE: (role: string) => `/workforce/role/${role}`,
  REGISTER: "/workforce/register",
  HEARTBEAT: (id: string) => `/workforce/${id}/heartbeat`,
  STATUS_UPDATE: (id: string) => `/workforce/${id}/status`,
  PROCESS_WORKFLOW: (id: string) => `/workforce/workflow/${id}/process`,
} as const;

export const TOOL_ROUTES = {
  CENTER: "/tools",
} as const;

export const TOOL_ENDPOINTS = {
  BASE: "/tools",
  EXECUTE: "/tools/execute",
  HEALTH: "/tools/health",
  EXECUTIONS: "/tools/executions",
  GET: (id: string) => `/tools/${id}`,
  CANCEL: (id: string) => `/tools/${id}/cancel`,
} as const;

export const SOFTWARE_ENGINEER_ROUTES = {
  WORKSPACE: "/software-engineer",
} as const;

export const SOFTWARE_ENGINEER_ENDPOINTS = {
  BASE: "/agents/software-engineer",
  EXECUTE: "/agents/software-engineer/execute",
  ANALYZE: "/agents/software-engineer/analyze",
  STATUS: "/agents/software-engineer/status",
  HISTORY: "/agents/software-engineer/history",
  APPROVE: "/agents/software-engineer/approve",
  REJECT: "/agents/software-engineer/reject",
  GET_TASK: (id: string) => `/agents/software-engineer/tasks/${id}`,
} as const;



export const APPROVAL_ROUTES = {
  GATE: "/approval",
} as const;

export const APPROVAL_ENDPOINTS = {
  BASE: "/approval",
  REQUEST: "/approval/request",
  PENDING: (executionId: string) => `/approval/pending/${executionId}`,
  DECIDE: (requestId: string) => `/approval/${requestId}/decide`,
  GET: (requestId: string) => `/approval/${requestId}`,
  CANCEL: (requestId: string) => `/approval/${requestId}/cancel`,
  STATS: "/approval/stats",
  AUTO_APPROVE: "/approval/auto-approve",
} as const;

export const DEPLOYMENT_ROUTES = {
  CENTER: "/deployment",
} as const;

export const DEPLOYMENT_ENDPOINTS = {
  ANALYZE: "/devops/analyze",
  GENERATE: "/devops/generate",
  REPORT: (taskId: string) => `/devops/report/${taskId}`,
  DOCKER: (taskId: string) => `/devops/docker/${taskId}`,
  GITHUB_ACTIONS: (taskId: string) => `/devops/github-actions/${taskId}`,
  KUBERNETES: (taskId: string) => `/devops/kubernetes/${taskId}`,
  TASKS: "/devops/tasks",
  TASK: (taskId: string) => `/devops/tasks/${taskId}`,
} as const;

export const LEARNING_ROUTES = {
  CENTER: "/learning",
} as const;

export const LEARNING_ENDPOINTS = {
  PROCESS: "/learning/process",
  PATTERNS: "/learning/patterns",
  EXPERIENCES: "/learning/experiences",
  RECOMMENDATIONS: "/learning/recommendations",
  FEEDBACK: "/learning/feedback",
  STATS: "/learning/stats",
  GROWTH: "/learning/growth",
  TASKS: "/learning/tasks",
} as const;

export const MONITORING_ROUTES = {
  DASHBOARD: "/monitoring",
} as const;

export const MONITORING_ENDPOINTS = {
  OVERVIEW: "/monitoring/overview",
  WORKFLOWS: "/monitoring/workflows",
  AGENTS: "/monitoring/agents",
  TOOLS: "/monitoring/tools",
  MEMORY: "/monitoring/memory",
  PROMPTS: "/monitoring/prompts",
  ANALYTICS: "/monitoring/analytics",
  HEALTH: "/monitoring/health",
  TIMELINE: "/monitoring/timeline",
  EXECUTIONS: "/monitoring/executions",
} as const;

export const STUDIO_ROUTES = {
  HOME: "/studio",
} as const;

export const STUDIO_ENDPOINTS = {
  WORKFLOWS: "/studio/workflows",
  WORKFLOW_GRAPH: (id: string) => `/studio/workflows/${id}/graph`,
  NODE_TEMPLATES: "/studio/workflows/node-templates",
  VALIDATE: "/studio/workflows/validate",
  PROMPTS: "/studio/prompts",
  PROMPT: (id: string) => `/studio/prompts/${id}`,
  PROMPT_HISTORY: (id: string) => `/studio/prompts/${id}/history`,
  PROMPT_TEST: (id: string) => `/studio/prompts/${id}/test`,
  PROMPT_ROLLBACK: (id: string) => `/studio/prompts/${id}/rollback`,
  REPLAY: (id: string) => `/studio/replay/${id}`,
  REPLAY_EVENTS: (id: string) => `/studio/replay/${id}/events`,
  AGENTS: "/studio/agents",
  AGENT: (id: string) => `/studio/agents/${id}`,
  AGENT_CONFIG: (id: string) => `/studio/agents/${id}/config`,
  AGENT_PERFORMANCE: (id: string) => `/studio/agents/${id}/performance`,
  WORKSPACE: "/studio/workspace",
  WORKSPACE_SEARCH: "/studio/workspace/search",
  WORKSPACE_RECENT: "/studio/workspace/recent",
  WORKSPACE_BOOKMARKS: "/studio/workspace/bookmarks",
} as const;

export const ORGANIZATION_ROUTES = {
  LIST: "/organizations",
  DETAIL: (id: string) => `/organizations/${id}`,
} as const;

export const ORGANIZATION_ENDPOINTS = {
  ORGANIZATIONS: "/organizations",
  ORGANIZATION: (id: string) => `/organizations/${id}`,
  REPOSITORIES: (orgId: string) => `/organizations/${orgId}/repositories`,
  REPOSITORY: (orgId: string, repoId: string) => `/organizations/${orgId}/repositories/${repoId}`,
  STATS: (orgId: string) => `/organizations/${orgId}/stats`,
  KNOWLEDGE: "/organizations/shared-learning",
  KNOWLEDGE_ITEM: (id: string) => `/organizations/shared-learning/${id}`,
  TEMPLATES: "/organizations/templates",
  TEMPLATE: (id: string) => `/organizations/templates/${id}`,
  USE_TEMPLATE: (id: string) => `/organizations/templates/${id}/use`,
  SEARCH: "/organizations/search",
  COMPARE: "/organizations/compare",
  GRAPH: "/organizations/graph",
  COLLABORATION: "/organizations/collaboration",
  ACTIVITY: "/organizations/activity",
  RECOMMENDATIONS: "/organizations/recommendations",
} as const;

export const DEVELOPER_ROUTES = {
  CENTER: "/developer",
} as const;

export const DEVELOPER_ENDPOINTS = {
  CONFIG: "/developer/config",
  CONFIG_SECTION: (section: string) => `/developer/config/${section}`,
  CONFIG_VALIDATE: "/developer/config/validate",
  PLUGINS: "/developer/plugins",
  PLUGIN: (id: string) => `/developer/plugins/${id}`,
  PLUGIN_ENABLE: (id: string) => `/developer/plugins/${id}/enable`,
  PLUGIN_DISABLE: (id: string) => `/developer/plugins/${id}/disable`,
  PLUGIN_CONFIG: (id: string) => `/developer/plugins/${id}/config`,
  TEMPLATES: "/developer/templates",
  TEMPLATE: (id: string) => `/developer/templates/${id}`,
  TEMPLATE_FILES: (id: string) => `/developer/templates/${id}/files`,
  SDK: (lang: string) => `/developer/sdk/${lang}`,
  SDK_QUICKSTART: (lang: string) => `/developer/sdk/${lang}/quickstart`,
  CLI_COMMANDS: "/developer/cli/commands",
  CLI_HELP: "/developer/cli/help",
  DIAGNOSTICS: "/developer/diagnostics",
  DOCTOR: "/developer/diagnostics/doctor",
  BACKUP: "/developer/backup",
  BACKUP_ITEM: (id: string) => `/developer/backup/${id}`,
  RESTORE: "/developer/backup/restore",
  PREREQUISITES: "/developer/installer/prerequisites",
  QUICKSTART: "/developer/installer/quickstart",
  GUIDE: "/developer/installer/guide",
  LOGS: "/developer/logs",
} as const;

export const PLUGIN_ROUTES = {
  MARKETPLACE: "/plugins",
} as const;

export const PLUGIN_ENDPOINTS = {
  LIST: "/plugins",
  MARKETPLACE: "/plugins/marketplace",
  FEATURED: "/plugins/featured",
  TRENDING: "/plugins/trending",
  CATEGORIES: "/plugins/categories",
  PLUGIN: (id: string) => `/plugins/${id}`,
  INSTALL: "/plugins/install",
  UNINSTALL: (id: string) => `/plugins/${id}/uninstall`,
  ENABLE: (id: string) => `/plugins/${id}/enable`,
  DISABLE: (id: string) => `/plugins/${id}/disable`,
  CONFIG: (id: string) => `/plugins/${id}/config`,
  VALIDATE: (id: string) => `/plugins/${id}/validate`,
  REVIEWS: (id: string) => `/plugins/${id}/reviews`,
  INSTALLED: "/plugins/installed",
  STATS: "/plugins/stats",
  SDK_DOCS: "/plugins/sdk/docs",
  TEMPLATES: "/plugins/templates",
} as const;

export const EXPERIENCE_ROUTES = {
  CENTER: "/experience",
} as const;

export const EXPERIENCE_ENDPOINTS = {
  NOTIFICATIONS: "/experience/notifications",
  NOTIFICATION_READ: (id: string) => `/experience/notifications/${id}/read`,
  NOTIFICATIONS_READ_ALL: "/experience/notifications/read-all",
  UNREAD_COUNT: "/experience/notifications/unread-count",
  ACTIVITY: "/experience/activity",
  ACTIVITY_ENTITY: (type: string, id: string) => `/experience/activity/entity/${type}/${id}`,
  SEARCH: "/experience/search",
  SEARCH_RECENT: "/experience/search/recent",
  SEARCH_POPULAR: "/experience/search/popular",
  SETTINGS: "/experience/settings",
  SETTING: (key: string) => `/experience/settings/${key}`,
  SETTINGS_RESET: "/experience/settings/reset",
  ONBOARDING_STEPS: "/experience/onboarding/steps",
  ONBOARDING_STATE: "/experience/onboarding/state",
  ONBOARDING_STEP: (id: string) => `/experience/onboarding/step/${id}`,
  ONBOARDING_SKIP: "/experience/onboarding/skip",
  TUTORIALS: "/experience/tutorials",
  TUTORIAL: (id: string) => `/experience/tutorials/${id}`,
  COMMAND_PALETTE: "/experience/command-palette",
  SHORTCUTS: "/experience/shortcuts",
} as const;

export const VALIDATION_ROUTES = {
  DASHBOARD: "/validation",
} as const;

export const VALIDATION_ENDPOINTS = {
  SYSTEM: "/validation/system",
  BENCHMARK: "/validation/benchmark",
  QUALITY: "/validation/quality",
  SECURITY: "/validation/security",
  E2E: "/validation/e2e",
  REPORT: "/validation/report",
} as const;
