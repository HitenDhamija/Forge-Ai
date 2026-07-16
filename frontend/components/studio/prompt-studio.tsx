'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useStudioStore } from '@/stores/studio-store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { EmptyState } from '@/components/ui/empty-state';
import {
  Search,
  Plus,
  Save,
  Play,
  RotateCcw,
  History,
  Tag,
  Variable,
  CheckCircle2,
  AlertCircle,
  Clock,
  FileText,
  ChevronRight,
  Diff,
  Loader2,
} from 'lucide-react';
import { studioService } from '@/services/studio.service';
import type { PromptTemplate, PromptTestResult, PromptVersion } from '@/types/studio';

const AVAILABLE_MODELS = [
  { id: 'gpt-4', name: 'GPT-4' },
  { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo' },
  { id: 'claude-3-opus', name: 'Claude 3 Opus' },
  { id: 'claude-3-sonnet', name: 'Claude 3 Sonnet' },
];

export function PromptStudio() {
  const { prompts, selectedPrompt, fetchPrompts, fetchPrompt, isLoading } = useStudioStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedModel, setSelectedModel] = useState('gpt-4');
  const [editContent, setEditContent] = useState('');
  const [editComment, setEditComment] = useState('');
  const [inputVars, setInputVars] = useState<Record<string, string>>({});
  const [testResult, setTestResult] = useState<PromptTestResult | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newPrompt, setNewPrompt] = useState({ name: '', description: '', content: '', tags: '' });
  const [isCreating, setIsCreating] = useState(false);
  const [showHistory, setShowHistory] = useState(true);
  const [compareVersions, setCompareVersions] = useState<[number, number] | null>(null);

  useEffect(() => {
    fetchPrompts();
  }, [fetchPrompts]);

  useEffect(() => {
    if (selectedPrompt) {
      setEditContent(selectedPrompt.content);
      setEditComment('');
      setTestResult(null);
      const vars: Record<string, string> = {};
      selectedPrompt.variables.forEach((v) => {
        vars[v] = '';
      });
      setInputVars(vars);
    }
  }, [selectedPrompt]);

  const filteredPrompts = useMemo(() => {
    if (!searchQuery) return prompts;
    const q = searchQuery.toLowerCase();
    return prompts.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.description.toLowerCase().includes(q) ||
        p.tags.some((t) => t.toLowerCase().includes(q))
    );
  }, [prompts, searchQuery]);

  const extractedVariables = useMemo(() => {
    const matches = editContent.match(/\{\{(\w+)\}\}/g);
    if (!matches) return [];
    const uniqueVars = Array.from(new Set(matches.map((m) => m.replace(/\{\{|\}\}/g, ''))));
    return uniqueVars;
  }, [editContent]);

  const handleSave = async () => {
    if (!selectedPrompt || !editComment.trim()) return;
    setIsSaving(true);
    try {
      await studioService.updatePrompt(selectedPrompt.id, editContent, editComment);
      await fetchPrompt(selectedPrompt.id);
      await fetchPrompts();
      setEditComment('');
    } catch (err) {
      console.error('Failed to save prompt:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleRunTest = async () => {
    if (!selectedPrompt) return;
    setIsTesting(true);
    try {
      const result = await studioService.testPrompt(selectedPrompt.id, selectedModel, inputVars);
      setTestResult(result);
    } catch (err) {
      console.error('Failed to run test:', err);
    } finally {
      setIsTesting(false);
    }
  };

  const handleCreatePrompt = async () => {
    if (!newPrompt.name.trim() || !newPrompt.content.trim()) return;
    setIsCreating(true);
    try {
      const tags = newPrompt.tags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean);
      const promptId = await studioService.createPrompt({
        name: newPrompt.name,
        description: newPrompt.description,
        content: newPrompt.content,
        tags,
      });
      await fetchPrompts();
      await fetchPrompt(promptId);
      setShowCreateModal(false);
      setNewPrompt({ name: '', description: '', content: '', tags: '' });
    } catch (err) {
      console.error('Failed to create prompt:', err);
    } finally {
      setIsCreating(false);
    }
  };

  const handleRollback = async (version: number) => {
    if (!selectedPrompt) return;
    try {
      await studioService.rollbackPrompt(selectedPrompt.id, version);
      await fetchPrompt(selectedPrompt.id);
      await fetchPrompts();
    } catch (err) {
      console.error('Failed to rollback:', err);
    }
  };

  const renderHighlightedContent = (content: string) => {
    const parts = content.split(/(\{\{\w+\}\})/g);
    return parts.map((part, i) => {
      if (/\{\{\w+\}\}/.test(part)) {
        return (
          <span key={i} className="inline-flex items-center rounded bg-accent/20 px-1.5 py-0.5 text-xs font-medium text-accent">
            <Variable className="mr-1 h-3 w-3" />
            {part.replace(/\{\{|\}\}/g, '')}
          </span>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex flex-1 gap-4 min-h-0">
        {/* Prompt List Panel */}
        <div className="flex w-72 flex-shrink-0 flex-col gap-2">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-text">Prompts</h2>
            <Button size="sm" leftIcon={<Plus className="h-4 w-4" />} onClick={() => setShowCreateModal(true)}>
              New
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
            <input
              type="text"
              placeholder="Search prompts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-9 w-full rounded-md border border-border bg-surface pl-9 pr-3 text-sm text-text placeholder:text-text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            />
          </div>
          <div className="flex-1 space-y-2 overflow-y-auto">
            {filteredPrompts.length === 0 ? (
              <EmptyState icon={<FileText className="h-10 w-10" />} title="No prompts" description="Create your first prompt template" />
            ) : (
              filteredPrompts.map((prompt) => (
                <Card
                  key={prompt.id}
                  className={`cursor-pointer transition-colors hover:border-accent ${
                    selectedPrompt?.id === prompt.id ? 'border-accent bg-accent/5' : ''
                  }`}
                  onClick={() => fetchPrompt(prompt.id)}
                >
                  <CardContent className="p-3">
                    <div className="flex items-start justify-between">
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-text">{prompt.name}</p>
                        <p className="mt-0.5 truncate text-xs text-text-muted">{prompt.description}</p>
                      </div>
                      <Badge variant="secondary" className="ml-2 flex-shrink-0">
                        v{prompt.current_version}
                      </Badge>
                    </div>
                    {prompt.tags.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {prompt.tags.slice(0, 3).map((tag) => (
                          <Badge key={tag} variant="outline" className="text-[10px]">
                            {tag}
                          </Badge>
                        ))}
                        {prompt.tags.length > 3 && (
                          <Badge variant="outline" className="text-[10px]">
                            +{prompt.tags.length - 3}
                          </Badge>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>

        {/* Prompt Editor Panel */}
        <div className="flex min-w-0 flex-1 flex-col gap-2">
          {selectedPrompt ? (
            <>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <h2 className="text-lg font-semibold text-text">{selectedPrompt.name}</h2>
                  <Badge>Version {selectedPrompt.current_version}</Badge>
                  <Badge variant="secondary">{selectedPrompt.versions_count} versions</Badge>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    leftIcon={<History className="h-4 w-4" />}
                    onClick={() => setShowHistory(!showHistory)}
                  >
                    History
                  </Button>
                </div>
              </div>
              <div className="flex flex-wrap gap-1">
                {selectedPrompt.tags.map((tag) => (
                  <Badge key={tag} variant="outline">
                    <Tag className="mr-1 h-3 w-3" />
                    {tag}
                  </Badge>
                ))}
              </div>
              <div className="flex-1 min-h-0">
                <div className="relative h-full">
                  <div className="absolute inset-0 overflow-auto rounded-md border border-border bg-surface p-4 font-mono text-sm leading-relaxed text-text">
                    {renderHighlightedContent(editContent)}
                  </div>
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    className="absolute inset-0 h-full w-full resize-none rounded-md border border-border bg-transparent p-4 font-mono text-sm leading-relaxed text-transparent caret-text focus:outline-none focus:ring-1 focus:ring-accent"
                    spellCheck={false}
                  />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Input
                  placeholder="Version comment..."
                  value={editComment}
                  onChange={(e) => setEditComment(e.target.value)}
                  className="flex-1"
                />
                <Button
                  leftIcon={<Save className="h-4 w-4" />}
                  isLoading={isSaving}
                  disabled={!editComment.trim()}
                  onClick={handleSave}
                >
                  Save
                </Button>
              </div>
              {extractedVariables.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  <span className="text-xs text-text-muted">Variables detected:</span>
                  {extractedVariables.map((v) => (
                    <Badge key={v} variant="secondary" className="text-[10px]">
                      <Variable className="mr-1 h-3 w-3" />
                      {v}
                    </Badge>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="flex h-full items-center justify-center">
              <EmptyState
                icon={<FileText className="h-12 w-12" />}
                title="Select a prompt"
                description="Choose a prompt from the list to edit and test"
              />
            </div>
          )}
        </div>

        {/* Testing Panel */}
        <div className="flex w-80 flex-shrink-0 flex-col gap-2">
          <h2 className="text-lg font-semibold text-text">Test</h2>
          {selectedPrompt ? (
            <>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-text">Model</label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="h-10 w-full rounded-md border border-border bg-surface px-3 text-sm text-text focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                >
                  {AVAILABLE_MODELS.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex-1 space-y-3 overflow-y-auto">
                <p className="text-sm font-medium text-text">Input Variables</p>
                {Object.keys(inputVars).length === 0 ? (
                  <p className="text-xs text-text-muted">No variables in this prompt</p>
                ) : (
                  Object.entries(inputVars).map(([key, value]) => (
                    <Input
                      key={key}
                      label={key}
                      placeholder={`Enter value for {{${key}}}...`}
                      value={value}
                      onChange={(e) => setInputVars((prev) => ({ ...prev, [key]: e.target.value }))}
                    />
                  ))
                )}
              </div>
              <Button
                leftIcon={<Play className="h-4 w-4" />}
                isLoading={isTesting}
                className="w-full"
                onClick={handleRunTest}
              >
                Run Test
              </Button>
              {testResult && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">Result</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="rounded-md border border-border bg-surface p-3">
                      <p className="whitespace-pre-wrap text-sm text-text">{testResult.output}</p>
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      <div className="rounded-md border border-border p-2 text-center">
                        <p className="text-lg font-semibold text-text">{testResult.tokens_used}</p>
                        <p className="text-[10px] text-text-muted">Tokens</p>
                      </div>
                      <div className="rounded-md border border-border p-2 text-center">
                        <p className="text-lg font-semibold text-text">{testResult.latency_ms}ms</p>
                        <p className="text-[10px] text-text-muted">Latency</p>
                      </div>
                      <div className="rounded-md border border-border p-2 text-center">
                        <p className="text-lg font-semibold text-text">
                          {(testResult.confidence * 100).toFixed(0)}%
                        </p>
                        <p className="text-[10px] text-text-muted">Confidence</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <div className="flex h-full items-center justify-center">
              <EmptyState icon={<Play className="h-8 w-8" />} title="No prompt selected" description="Select a prompt to start testing" />
            </div>
          )}
        </div>
      </div>

      {/* Version History Panel */}
      {selectedPrompt && showHistory && (
        <Card className="flex-shrink-0">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm">Version History</CardTitle>
              {compareVersions && (
                <Button variant="ghost" size="sm" onClick={() => setCompareVersions(null)}>
                  Clear Compare
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="max-h-40 overflow-y-auto">
              <div className="space-y-1">
                {[...selectedPrompt.versions].reverse().map((version) => (
                  <div
                    key={version.version}
                    className={`flex items-center justify-between rounded-md border p-2 text-sm ${
                      version.version === selectedPrompt.current_version
                        ? 'border-accent bg-accent/5'
                        : 'border-border'
                    } ${
                      compareVersions &&
                      (version.version === compareVersions[0] || version.version === compareVersions[1])
                        ? 'ring-1 ring-accent'
                        : ''
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Badge variant={version.version === selectedPrompt.current_version ? 'default' : 'secondary'}>
                        v{version.version}
                      </Badge>
                      <span className="text-text-muted">{version.comment}</span>
                      <span className="flex items-center gap-1 text-xs text-text-muted">
                        <Clock className="h-3 w-3" />
                        {new Date(version.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          if (!compareVersions) {
                            setCompareVersions([version.version, version.version]);
                          } else if (compareVersions[0] === version.version) {
                            setCompareVersions(null);
                          } else {
                            setCompareVersions([compareVersions[0], version.version]);
                          }
                        }}
                      >
                        <Diff className="h-3 w-3" />
                      </Button>
                      {version.version !== selectedPrompt.current_version && (
                        <Button variant="ghost" size="sm" onClick={() => handleRollback(version.version)}>
                          <RotateCcw className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Create Prompt Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-lg">
            <CardHeader>
              <CardTitle>Create New Prompt</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                label="Name"
                placeholder="e.g., Code Review Assistant"
                value={newPrompt.name}
                onChange={(e) => setNewPrompt((p) => ({ ...p, name: e.target.value }))}
              />
              <Input
                label="Description"
                placeholder="A brief description of what this prompt does"
                value={newPrompt.description}
                onChange={(e) => setNewPrompt((p) => ({ ...p, description: e.target.value }))}
              />
              <Textarea
                label="Prompt Content"
                placeholder="Enter your prompt template... Use {{variable}} for dynamic values"
                value={newPrompt.content}
                onChange={(e) => setNewPrompt((p) => ({ ...p, content: e.target.value }))}
                className="min-h-[200px] font-mono text-sm"
              />
              <Input
                label="Tags (comma-separated)"
                placeholder="e.g., code-review, quality, refactor"
                value={newPrompt.tags}
                onChange={(e) => setNewPrompt((p) => ({ ...p, tags: e.target.value }))}
              />
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </Button>
                <Button
                  isLoading={isCreating}
                  disabled={!newPrompt.name.trim() || !newPrompt.content.trim()}
                  onClick={handleCreatePrompt}
                >
                  Create
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
