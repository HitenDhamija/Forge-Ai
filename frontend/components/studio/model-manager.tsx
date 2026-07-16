'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import {
  Brain,
  Download,
  Play,
  StopCircle,
  Trash2,
  RefreshCw,
  Search,
  HardDrive,
  Cpu,
  Zap,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  AlertTriangle,
  Settings,
  BarChart3,
  ChevronRight,
  Info,
} from 'lucide-react';

type ModelStatus = 'running' | 'stopped' | 'downloading' | 'error';

interface OllamaModel {
  id: string;
  name: string;
  version: string;
  size: number;
  status: ModelStatus;
  lastUsed: string;
  parameterSize?: string;
  quantization?: string;
  contextWindow?: number;
  parameters: {
    temperature: number;
    topP: number;
    topK: number;
    repeatPenalty: number;
  };
  metrics: {
    totalRequests: number;
    avgLatencyMs: number;
    tokensPerSecond: number;
    errorRate: number;
  };
}

interface DownloadProgress {
  modelId: string;
  modelName: string;
  progress: number;
  status: 'pending' | 'downloading' | 'completed' | 'error';
  speed?: string;
  eta?: string;
}

interface ModelStats {
  installedCount: number;
  runningCount: number;
  totalSize: number;
  gpuUsage: number;
}

const MOCK_INSTALLED_MODELS: OllamaModel[] = [
  {
    id: 'llama3.2:latest',
    name: 'llama3.2',
    version: 'latest',
    size: 4.7 * 1024 * 1024 * 1024,
    status: 'running',
    lastUsed: '2026-07-02T10:30:00Z',
    parameterSize: '3B',
    quantization: 'Q4_0',
    contextWindow: 131072,
    parameters: { temperature: 0.7, topP: 0.9, topK: 40, repeatPenalty: 1.1 },
    metrics: { totalRequests: 1247, avgLatencyMs: 45, tokensPerSecond: 85, errorRate: 0.02 },
  },
  {
    id: 'codellama:latest',
    name: 'codellama',
    version: 'latest',
    size: 7.4 * 1024 * 1024 * 1024,
    status: 'stopped',
    lastUsed: '2026-07-01T18:45:00Z',
    parameterSize: '7B',
    quantization: 'Q4_0',
    contextWindow: 16384,
    parameters: { temperature: 0.3, topP: 0.95, topK: 50, repeatPenalty: 1.0 },
    metrics: { totalRequests: 892, avgLatencyMs: 78, tokensPerSecond: 52, errorRate: 0.01 },
  },
  {
    id: 'mistral:latest',
    name: 'mistral',
    version: 'latest',
    size: 4.1 * 1024 * 1024 * 1024,
    status: 'stopped',
    lastUsed: '2026-06-30T09:15:00Z',
    parameterSize: '7B',
    quantization: 'Q4_K_M',
    contextWindow: 32768,
    parameters: { temperature: 0.7, topP: 0.9, topK: 40, repeatPenalty: 1.1 },
    metrics: { totalRequests: 456, avgLatencyMs: 52, tokensPerSecond: 72, errorRate: 0.03 },
  },
  {
    id: 'nomic-embed-text:latest',
    name: 'nomic-embed-text',
    version: 'latest',
    size: 0.27 * 1024 * 1024 * 1024,
    status: 'running',
    lastUsed: '2026-07-02T11:00:00Z',
    parameterSize: '137M',
    contextWindow: 8192,
    parameters: { temperature: 0.0, topP: 1.0, topK: 1, repeatPenalty: 1.0 },
    metrics: { totalRequests: 3421, avgLatencyMs: 12, tokensPerSecond: 1200, errorRate: 0.001 },
  },
  {
    id: 'phi3:latest',
    name: 'phi3',
    version: 'latest',
    size: 2.2 * 1024 * 1024 * 1024,
    status: 'stopped',
    lastUsed: '2026-06-28T14:20:00Z',
    parameterSize: '3.8B',
    quantization: 'Q4_0',
    contextWindow: 131072,
    parameters: { temperature: 0.5, topP: 0.9, topK: 40, repeatPenalty: 1.1 },
    metrics: { totalRequests: 123, avgLatencyMs: 32, tokensPerSecond: 98, errorRate: 0.05 },
  },
];

const MOCK_AVAILABLE_MODELS: { name: string; size: number; description: string; tags: string[] }[] = [
  { name: 'llama3.1:70b', size: 40 * 1024 * 1024 * 1024, description: 'Large language model with 70B parameters', tags: ['general', 'large'] },
  { name: 'gemma2:latest', size: 5.4 * 1024 * 1024 * 1024, description: 'Google Gemma 2 model', tags: ['general', 'google'] },
  { name: 'qwen2.5:latest', size: 4.4 * 1024 * 1024 * 1024, description: 'Alibaba Qwen 2.5 model', tags: ['general', 'multilingual'] },
  { name: 'deepseek-coder:latest', size: 7.8 * 1024 * 1024 * 1024, description: 'Code-specialized model', tags: ['coding', 'specialized'] },
  { name: 'phi3.5:latest', size: 2.4 * 1024 * 1024 * 1024, description: 'Microsoft Phi-3.5 model', tags: ['small', 'efficient'] },
  { name: 'stablelm2:latest', size: 1.7 * 1024 * 1024 * 1024, description: 'Stability AI language model', tags: ['small', 'general'] },
];

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const gb = bytes / (1024 * 1024 * 1024);
  if (gb >= 1) return `${gb.toFixed(2)} GB`;
  const mb = bytes / (1024 * 1024);
  return `${mb.toFixed(2)} MB`;
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

const STATUS_CONFIG: Record<ModelStatus, { label: string; variant: 'success' | 'secondary' | 'warning' | 'destructive'; dotColor: string }> = {
  running: { label: 'Running', variant: 'success', dotColor: 'bg-success' },
  stopped: { label: 'Stopped', variant: 'secondary', dotColor: 'bg-text-muted' },
  downloading: { label: 'Downloading', variant: 'warning', dotColor: 'bg-warning' },
  error: { label: 'Error', variant: 'destructive', dotColor: 'bg-danger' },
};

function StatsOverview({ stats, currentModel, isLoading }: { stats: ModelStats; currentModel: string | null; isLoading: boolean }) {
  const statCards = [
    { label: 'Installed Models', value: stats.installedCount, icon: Brain, color: 'text-info' },
    { label: 'Running Models', value: stats.runningCount, icon: Zap, color: 'text-success' },
    { label: 'Total Size', value: formatBytes(stats.totalSize), icon: HardDrive, color: 'text-warning' },
    { label: 'GPU Usage', value: `${stats.gpuUsage}%`, icon: Cpu, color: 'text-accent' },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase text-text-muted">Model Overview</h2>
        {currentModel && (
          <Badge variant="outline" className="gap-1">
            <Zap className="h-3 w-3" />
            Active: {currentModel}
          </Badge>
        )}
      </div>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {statCards.map((stat) => (
          <Card key={stat.label}>
            <CardContent className="p-4">
              {isLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-8 w-16" />
                </div>
              ) : (
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs font-medium text-text-muted">{stat.label}</p>
                    <p className="mt-1 text-2xl font-bold text-text">{stat.value}</p>
                  </div>
                  <stat.icon className={`h-5 w-5 ${stat.color}`} />
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function ModelListPanel({
  models,
  selectedModel,
  onSelectModel,
  onStartModel,
  onStopModel,
  onRemoveModel,
  isLoading,
}: {
  models: OllamaModel[];
  selectedModel: OllamaModel | null;
  onSelectModel: (model: OllamaModel) => void;
  onStartModel: (modelId: string) => void;
  onStopModel: (modelId: string) => void;
  onRemoveModel: (modelId: string) => void;
  isLoading: boolean;
}) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredModels = models.filter(
    (model) =>
      model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      model.parameterSize?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex h-full flex-col border-r border-border">
      <div className="border-b border-border p-4">
        <h2 className="mb-3 text-sm font-semibold uppercase text-text-muted">Installed Models</h2>
        <Input
          placeholder="Search models..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          leftIcon={<Search className="h-4 w-4" />}
        />
      </div>
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="space-y-2 p-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="space-y-2 rounded-lg border border-border p-3">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
                <Skeleton className="h-3 w-2/3" />
              </div>
            ))}
          </div>
        ) : filteredModels.length === 0 ? (
          <EmptyState
            icon={<Brain className="h-10 w-10" />}
            title="No models found"
            description={searchQuery ? 'Try a different search term' : 'No models installed'}
          />
        ) : (
          <div className="space-y-1 p-2">
            {filteredModels.map((model) => {
              const isSelected = selectedModel?.id === model.id;
              const statusConfig = STATUS_CONFIG[model.status];
              return (
                <button
                  key={model.id}
                  onClick={() => onSelectModel(model)}
                  className={`flex w-full items-start gap-3 rounded-lg p-3 text-left transition-colors ${
                    isSelected
                      ? 'bg-accent/10 border border-accent/30'
                      : 'hover:bg-surface-hover border border-transparent'
                  }`}
                >
                  <div className="mt-1 flex-shrink-0">
                    <div className={`h-2.5 w-2.5 rounded-full ${statusConfig.dotColor}`} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="truncate text-sm font-medium text-text">{model.name}</span>
                      <Badge variant={statusConfig.variant} className="text-[10px] px-1.5 py-0">
                        {statusConfig.label}
                      </Badge>
                    </div>
                    <div className="mt-1 flex items-center gap-2 text-xs text-text-muted">
                      <span>{model.parameterSize}</span>
                      <span>•</span>
                      <span>{formatBytes(model.size)}</span>
                    </div>
                    <div className="mt-1 flex items-center gap-1 text-xs text-text-muted">
                      <Clock className="h-3 w-3" />
                      <span>{formatDate(model.lastUsed)}</span>
                    </div>
                  </div>
                  <div className="flex flex-col gap-1">
                    {model.status === 'stopped' ? (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation();
                          onStartModel(model.id);
                        }}
                        className="h-7 w-7 p-0"
                      >
                        <Play className="h-3.5 w-3.5" />
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation();
                          onStopModel(model.id);
                        }}
                        className="h-7 w-7 p-0"
                      >
                        <StopCircle className="h-3.5 w-3.5" />
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => {
                        e.stopPropagation();
                        onRemoveModel(model.id);
                      }}
                      className="h-7 w-7 p-0 text-danger hover:text-danger"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                  {isSelected && <ChevronRight className="mt-1 h-4 w-4 flex-shrink-0 text-accent" />}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function ModelDetailsPanel({ model }: { model: OllamaModel }) {
  const statusConfig = STATUS_CONFIG[model.status];

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-xl">{model.name}</CardTitle>
                <CardDescription className="mt-1">
                  Version: {model.version} • {model.parameterSize} • {model.quantization}
                </CardDescription>
              </div>
              <Badge variant={statusConfig.variant}>{statusConfig.label}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex items-center gap-2 text-text-muted">
                <HardDrive className="h-4 w-4" />
                <span className="font-medium">Size:</span>
                <span>{formatBytes(model.size)}</span>
              </div>
              <div className="flex items-center gap-2 text-text-muted">
                <Clock className="h-4 w-4" />
                <span className="font-medium">Last Used:</span>
                <span>{formatDate(model.lastUsed)}</span>
              </div>
              {model.contextWindow && (
                <div className="flex items-center gap-2 text-text-muted">
                  <Info className="h-4 w-4" />
                  <span className="font-medium">Context Window:</span>
                  <span>{model.contextWindow.toLocaleString()} tokens</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Settings className="h-4 w-4" />
              Parameters
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-text">Temperature</p>
                  <p className="text-xs text-text-muted">Controls randomness</p>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-24 overflow-hidden rounded-full bg-surface-hover">
                    <div
                      className="h-full bg-accent"
                      style={{ width: `${(model.parameters.temperature / 2) * 100}%` }}
                    />
                  </div>
                  <span className="w-8 text-right text-sm font-mono text-text">{model.parameters.temperature}</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-text">Top P</p>
                  <p className="text-xs text-text-muted">Nucleus sampling</p>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-24 overflow-hidden rounded-full bg-surface-hover">
                    <div
                      className="h-full bg-accent"
                      style={{ width: `${model.parameters.topP * 100}%` }}
                    />
                  </div>
                  <span className="w-8 text-right text-sm font-mono text-text">{model.parameters.topP}</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-text">Top K</p>
                  <p className="text-xs text-text-muted">Token sampling limit</p>
                </div>
                <span className="text-sm font-mono text-text">{model.parameters.topK}</span>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-text">Repeat Penalty</p>
                  <p className="text-xs text-text-muted">Repetition penalty factor</p>
                </div>
                <span className="text-sm font-mono text-text">{model.parameters.repeatPenalty}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <BarChart3 className="h-4 w-4" />
              Performance Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div className="space-y-1">
                <p className="text-xs font-medium uppercase text-text-muted">Total Requests</p>
                <p className="text-2xl font-bold text-text">{model.metrics.totalRequests.toLocaleString()}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-medium uppercase text-text-muted">Avg Latency</p>
                <p className="text-2xl font-bold text-info">{model.metrics.avgLatencyMs}ms</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-medium uppercase text-text-muted">Tokens/sec</p>
                <p className="text-2xl font-bold text-success">{model.metrics.tokensPerSecond}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-medium uppercase text-text-muted">Error Rate</p>
                <p className="text-2xl font-bold text-danger">{(model.metrics.errorRate * 100).toFixed(1)}%</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <BarChart3 className="h-4 w-4" />
              Usage Statistics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-text-muted">Requests today</span>
                <span className="font-medium text-text">{Math.floor(model.metrics.totalRequests * 0.1)}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-text-muted">Avg tokens per request</span>
                <span className="font-medium text-text">{Math.floor(1024 + Math.random() * 2048)}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-text-muted">Peak latency today</span>
                <span className="font-medium text-text">{model.metrics.avgLatencyMs * 1.5}ms</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-text-muted">Success rate</span>
                <span className="font-medium text-success">{((1 - model.metrics.errorRate) * 100).toFixed(1)}%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function DownloadSection({
  availableModels,
  downloads,
  onDownload,
  onCancelDownload,
  searchQuery,
  onSearchChange,
}: {
  availableModels: typeof MOCK_AVAILABLE_MODELS;
  downloads: DownloadProgress[];
  onDownload: (modelName: string) => void;
  onCancelDownload: (modelId: string) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
}) {
  const filteredModels = availableModels.filter(
    (model) =>
      model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      model.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      model.tags.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <Card className="mt-6">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-base">
              <Download className="h-4 w-4" />
              Download Models
            </CardTitle>
            <CardDescription className="mt-1">
              Browse and download available Ollama models
            </CardDescription>
          </div>
          <Button variant="outline" size="sm" leftIcon={<RefreshCw className="h-4 w-4" />}>
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="mb-4">
          <Input
            placeholder="Search available models..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            leftIcon={<Search className="h-4 w-4" />}
          />
        </div>

        {downloads.length > 0 && (
          <div className="mb-6 space-y-3">
            <h3 className="text-sm font-medium text-text-muted">Active Downloads</h3>
            {downloads.map((download) => (
              <div
                key={download.modelId}
                className="rounded-lg border border-border bg-surface p-3"
              >
                <div className="mb-2 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {download.status === 'downloading' && (
                      <Loader2 className="h-4 w-4 animate-spin text-info" />
                    )}
                    {download.status === 'completed' && (
                      <CheckCircle className="h-4 w-4 text-success" />
                    )}
                    {download.status === 'error' && (
                      <XCircle className="h-4 w-4 text-danger" />
                    )}
                    <span className="text-sm font-medium text-text">{download.modelName}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {download.speed && (
                      <span className="text-xs text-text-muted">{download.speed}</span>
                    )}
                    {download.eta && (
                      <span className="text-xs text-text-muted">ETA: {download.eta}</span>
                    )}
                    {download.status === 'downloading' && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onCancelDownload(download.modelId)}
                        className="h-6 px-2"
                      >
                        Cancel
                      </Button>
                    )}
                  </div>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-surface-hover">
                  <div
                    className={`h-full transition-all ${
                      download.status === 'error'
                        ? 'bg-danger'
                        : download.status === 'completed'
                        ? 'bg-success'
                        : 'bg-info'
                    }`}
                    style={{ width: `${download.progress}%` }}
                  />
                </div>
                <p className="mt-1 text-right text-xs text-text-muted">{download.progress}%</p>
              </div>
            ))}
          </div>
        )}

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {filteredModels.map((model) => {
            const activeDownload = downloads.find((d) => d.modelName === model.name);
            const isDownloading = activeDownload?.status === 'downloading';
            return (
              <div
                key={model.name}
                className="rounded-lg border border-border bg-surface p-4 transition-colors hover:bg-surface-hover"
              >
                <div className="mb-2 flex items-start justify-between">
                  <h4 className="text-sm font-medium text-text">{model.name}</h4>
                  <Badge variant="outline" className="text-[10px]">
                    {formatBytes(model.size)}
                  </Badge>
                </div>
                <p className="mb-3 text-xs text-text-muted">{model.description}</p>
                <div className="mb-3 flex flex-wrap gap-1">
                  {model.tags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="text-[10px]">
                      {tag}
                    </Badge>
                  ))}
                </div>
                <Button
                  size="sm"
                  variant={activeDownload?.status === 'completed' ? 'secondary' : 'default'}
                  disabled={isDownloading || activeDownload?.status === 'completed'}
                  isLoading={isDownloading}
                  onClick={() => onDownload(model.name)}
                  className="w-full"
                >
                  {activeDownload?.status === 'completed' ? (
                    'Installed'
                  ) : isDownloading ? (
                    'Downloading...'
                  ) : (
                    <>
                      <Download className="mr-1 h-3.5 w-3.5" />
                      Download
                    </>
                  )}
                </Button>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

export function ModelManager() {
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<OllamaModel | null>(null);
  const [availableModels] = useState(MOCK_AVAILABLE_MODELS);
  const [downloads, setDownloads] = useState<DownloadProgress[]>([]);
  const [downloadSearch, setDownloadSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [currentModel, setCurrentModel] = useState<string | null>(null);

  useEffect(() => {
    const loadModels = async () => {
      setIsLoading(true);
      await new Promise((r) => setTimeout(r, 800));
      setModels(MOCK_INSTALLED_MODELS);
      setCurrentModel('llama3.2');
      setIsLoading(false);
    };
    loadModels();
  }, []);

  const stats: ModelStats = {
    installedCount: models.length,
    runningCount: models.filter((m) => m.status === 'running').length,
    totalSize: models.reduce((acc, m) => acc + m.size, 0),
    gpuUsage: 67,
  };

  const handleStartModel = useCallback((modelId: string) => {
    setModels((prev) =>
      prev.map((m) => (m.id === modelId ? { ...m, status: 'running' as ModelStatus } : m))
    );
  }, []);

  const handleStopModel = useCallback((modelId: string) => {
    setModels((prev) =>
      prev.map((m) => (m.id === modelId ? { ...m, status: 'stopped' as ModelStatus } : m))
    );
  }, []);

  const handleRemoveModel = useCallback(
    (modelId: string) => {
      setModels((prev) => prev.filter((m) => m.id !== modelId));
      if (selectedModel?.id === modelId) {
        setSelectedModel(null);
      }
    },
    [selectedModel]
  );

  const handleDownload = useCallback((modelName: string) => {
    const model = MOCK_AVAILABLE_MODELS.find((m) => m.name === modelName);
    if (!model) return;

    const downloadId = `dl-${Date.now()}`;
    const newDownload: DownloadProgress = {
      modelId: downloadId,
      modelName: model.name,
      progress: 0,
      status: 'downloading',
      speed: '0 MB/s',
      eta: 'Calculating...',
    };

    setDownloads((prev) => [...prev, newDownload]);

    const interval = setInterval(() => {
      setDownloads((prev) =>
        prev.map((d) => {
          if (d.modelId !== downloadId) return d;
          const newProgress = d.progress + Math.random() * 15;
          if (newProgress >= 100) {
            clearInterval(interval);
            return {
              ...d,
              progress: 100,
              status: 'completed',
              speed: undefined,
              eta: undefined,
            };
          }
          return {
            ...d,
            progress: Math.floor(newProgress),
            speed: `${(Math.random() * 50 + 10).toFixed(1)} MB/s`,
            eta: `${Math.floor((100 - newProgress) / 10)}s`,
          };
        })
      );
    }, 500);
  }, []);

  const handleCancelDownload = useCallback((modelId: string) => {
    setDownloads((prev) => prev.filter((d) => d.modelId !== modelId));
  }, []);

  return (
    <div className="flex h-full flex-col">
      <StatsOverview stats={stats} currentModel={currentModel} isLoading={isLoading} />

      <div className="mt-6 flex min-h-0 flex-1">
        <div className="w-80 flex-shrink-0">
          <ModelListPanel
            models={models}
            selectedModel={selectedModel}
            onSelectModel={setSelectedModel}
            onStartModel={handleStartModel}
            onStopModel={handleStopModel}
            onRemoveModel={handleRemoveModel}
            isLoading={isLoading}
          />
        </div>

        <div className="flex min-w-0 flex-1">
          {selectedModel ? (
            <ModelDetailsPanel model={selectedModel} />
          ) : (
            <div className="flex h-full flex-1 items-center justify-center">
              <EmptyState
                icon={<Brain className="h-12 w-12" />}
                title="Select a model"
                description="Choose a model from the list to view details and manage parameters"
              />
            </div>
          )}
        </div>
      </div>

      <DownloadSection
        availableModels={availableModels}
        downloads={downloads}
        onDownload={handleDownload}
        onCancelDownload={handleCancelDownload}
        searchQuery={downloadSearch}
        onSearchChange={setDownloadSearch}
      />
    </div>
  );
}
