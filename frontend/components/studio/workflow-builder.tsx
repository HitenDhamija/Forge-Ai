'use client';

import React from 'react';
import { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { apiClient } from '@/services/api';
import { API_ENDPOINTS } from '@/config/constants';
import { useStudioStore } from '@/stores/studio-store';
import {
  Play,
  Target,
  Users,
  Bot,
  GitBranch,
  CheckCircle,
  RefreshCw,
  Wrench,
  Database,
  Zap,
  CircleStop,
  Plus,
  Save,
  Trash2,
  X,
  ArrowDown,
  GripVertical,
  Loader2,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Link2,
  Settings,
  FolderOpen,
  FileText,
  ChevronDown,
} from 'lucide-react';
import type { NodeType, WorkflowNode, WorkflowEdge } from '@/types/studio';

interface NodeTypeInfo {
  type: NodeType;
  label: string;
  icon: React.ReactNode;
  color: string;
  bgClass: string;
  borderClass: string;
  textClass: string;
}

const NODE_TYPES: NodeTypeInfo[] = [
  { type: 'start', label: 'Start', icon: <Play className="h-4 w-4" />, color: 'green', bgClass: 'bg-green-500/10', borderClass: 'border-green-500', textClass: 'text-green-500' },
  { type: 'planner', label: 'Planner', icon: <Target className="h-4 w-4" />, color: 'blue', bgClass: 'bg-blue-500/10', borderClass: 'border-blue-500', textClass: 'text-blue-500' },
  { type: 'supervisor', label: 'Supervisor', icon: <Users className="h-4 w-4" />, color: 'purple', bgClass: 'bg-purple-500/10', borderClass: 'border-purple-500', textClass: 'text-purple-500' },
  { type: 'agent', label: 'Agent', icon: <Bot className="h-4 w-4" />, color: 'indigo', bgClass: 'bg-indigo-500/10', borderClass: 'border-indigo-500', textClass: 'text-indigo-500' },
  { type: 'decision', label: 'Decision', icon: <GitBranch className="h-4 w-4" />, color: 'yellow', bgClass: 'bg-yellow-500/10', borderClass: 'border-yellow-500', textClass: 'text-yellow-500' },
  { type: 'approval', label: 'Approval', icon: <CheckCircle className="h-4 w-4" />, color: 'orange', bgClass: 'bg-orange-500/10', borderClass: 'border-orange-500', textClass: 'text-orange-500' },
  { type: 'reflection', label: 'Reflection', icon: <RefreshCw className="h-4 w-4" />, color: 'pink', bgClass: 'bg-pink-500/10', borderClass: 'border-pink-500', textClass: 'text-pink-500' },
  { type: 'tool', label: 'Tool', icon: <Wrench className="h-4 w-4" />, color: 'cyan', bgClass: 'bg-cyan-500/10', borderClass: 'border-cyan-500', textClass: 'text-cyan-500' },
  { type: 'memory', label: 'Memory', icon: <Database className="h-4 w-4" />, color: 'teal', bgClass: 'bg-teal-500/10', borderClass: 'border-teal-500', textClass: 'text-teal-500' },
  { type: 'execution', label: 'Execution', icon: <Zap className="h-4 w-4" />, color: 'red', bgClass: 'bg-red-500/10', borderClass: 'border-red-500', textClass: 'text-red-500' },
  { type: 'end', label: 'End', icon: <CircleStop className="h-4 w-4" />, color: 'gray', bgClass: 'bg-gray-500/10', borderClass: 'border-gray-500', textClass: 'text-gray-500' },
];

const STATUS_CONFIG: Record<string, { bg: string; text: string; dot: string; label: string }> = {
  idle: { bg: 'bg-gray-500/10', text: 'text-gray-500', dot: 'bg-gray-500', label: 'Idle' },
  running: { bg: 'bg-blue-500/10', text: 'text-blue-500', dot: 'bg-blue-500 animate-pulse', label: 'Running' },
  completed: { bg: 'bg-green-500/10', text: 'text-green-500', dot: 'bg-green-500', label: 'Completed' },
  failed: { bg: 'bg-red-500/10', text: 'text-red-500', dot: 'bg-red-500', label: 'Failed' },
  waiting: { bg: 'bg-yellow-500/10', text: 'text-yellow-500', dot: 'bg-yellow-500', label: 'Waiting' },
};

const DEFAULT_NODES: WorkflowNode[] = [
  { id: 'start-1', type: 'start', label: 'Start', position: { x: 0, y: 0 }, data: {}, status: 'idle' },
  { id: 'planner-1', type: 'planner', label: 'Plan Task', position: { x: 0, y: 1 }, data: { model: 'gpt-4' }, status: 'idle' },
  { id: 'agent-1', type: 'agent', label: 'Execute', position: { x: 0, y: 2 }, data: { role: 'executor' }, status: 'idle' },
  { id: 'end-1', type: 'end', label: 'End', position: { x: 0, y: 3 }, data: {}, status: 'idle' },
];

const DEFAULT_EDGES: WorkflowEdge[] = [
  { id: 'e-start-planner', source: 'start-1', target: 'planner-1', label: '' },
  { id: 'e-planner-agent', source: 'planner-1', target: 'agent-1', label: '' },
  { id: 'e-agent-end', source: 'agent-1', target: 'end-1', label: '' },
];

function getNodeTypeInfo(type: NodeType): NodeTypeInfo {
  return NODE_TYPES.find((t) => t.type === type) || NODE_TYPES[0];
}

function generateId(type: string): string {
  return `${type}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

interface WorkflowBuilderProps {
  workflowId?: string;
  onSave?: (nodes: WorkflowNode[], edges: WorkflowEdge[]) => void;
  onValidate?: (nodes: WorkflowNode[], edges: WorkflowEdge[]) => boolean;
}

export function WorkflowBuilder({ workflowId, onSave, onValidate }: WorkflowBuilderProps) {
  const {
    workflowGraph, setSelectedNode, selectedNodeId, isExecuting, executingNodeId, executeWorkflow, executionResults,
    savedWorkflows, currentWorkflowId, currentWorkflowName, currentWorkflowDescription, currentProjectId,
    loadSavedWorkflows, saveCurrentWorkflow, loadWorkflow, deleteWorkflow,
    setCurrentWorkflowName, setCurrentWorkflowDescription, setCurrentProjectId, newWorkflow,
  } = useStudioStore();

  const [nodes, setNodes] = useState<WorkflowNode[]>(DEFAULT_NODES);
  const [edges, setEdges] = useState<WorkflowEdge[]>(DEFAULT_EDGES);
  const [selectedNode, setSelectedNodeLocal] = useState<WorkflowNode | null>(null);
  const [connectingFrom, setConnectingFrom] = useState<string | null>(null);
  const [zoom, setZoom] = useState(100);
  const [isSaving, setIsSaving] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [projects, setProjects] = useState<Array<{ id: string; name: string }>>([]);
  const [viewingResult, setViewingResult] = useState<{
    node_id: string;
    label: string;
    node_type: string;
    status: string;
    output: Record<string, unknown>;
    duration_ms: number;
    error?: string;
    llm_model?: string;
    tokens_used?: number;
  } | null>(null);
  const canvasRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    apiClient.get(API_ENDPOINTS.PROJECTS.LIST).then((res: any) => {
      const data = res.data;
      const list = Array.isArray(data) ? data : data?.data || [];
      setProjects(list.map((p: any) => ({ id: p.id, name: p.name })));
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (workflowGraph) {
      setNodes(workflowGraph.nodes.length > 0 ? workflowGraph.nodes : DEFAULT_NODES);
      setEdges(workflowGraph.edges.length > 0 ? workflowGraph.edges : DEFAULT_EDGES);
    }
  }, [workflowGraph]);

  useEffect(() => {
    loadSavedWorkflows(currentProjectId || undefined);
  }, [currentProjectId]);

  const nodePositions = useMemo(() => {
    const posMap = new Map<string, { col: number; row: number }>();
    nodes.forEach((node) => {
      posMap.set(node.id, { col: node.position.x, row: node.position.y });
    });
    return posMap;
  }, [nodes]);

  const getSortedNodesByRow = useCallback(() => {
    return [...nodes].sort((a, b) => {
      const rowDiff = a.position.y - b.position.y;
      if (rowDiff !== 0) return rowDiff;
      return a.position.x - b.position.x;
    });
  }, [nodes]);

  const rows = useMemo(() => {
    const sorted = getSortedNodesByRow();
    const rowMap = new Map<number, WorkflowNode[]>();
    sorted.forEach((node) => {
      const row = node.position.y;
      if (!rowMap.has(row)) rowMap.set(row, []);
      rowMap.get(row)!.push(node);
    });
    return Array.from(rowMap.entries()).sort(([a], [b]) => a - b);
  }, [getSortedNodesByRow]);

  const addNode = useCallback((type: NodeType) => {
    const typeInfo = getNodeTypeInfo(type);
    const maxRow = nodes.reduce((max, n) => Math.max(max, n.position.y), -1);
    const newNode: WorkflowNode = {
      id: generateId(type),
      type,
      label: typeInfo.label,
      position: { x: 0, y: maxRow + 1 },
      data: {},
      status: 'idle',
    };
    setNodes((prev) => [...prev, newNode]);
  }, [nodes]);

  const handleSelectNode = useCallback((node: WorkflowNode) => {
    setSelectedNodeLocal(node);
    setSelectedNode(node.id);
  }, [setSelectedNode]);

  const handleDeselectNode = useCallback(() => {
    setSelectedNodeLocal(null);
    setSelectedNode(null);
  }, [setSelectedNode]);

  const handleUpdateNode = useCallback((updates: Partial<WorkflowNode>) => {
    if (!selectedNode) return;
    const updated = { ...selectedNode, ...updates };
    setSelectedNodeLocal(updated);
    setNodes((prev) => prev.map((n) => (n.id === selectedNode.id ? updated : n)));
  }, [selectedNode]);

  const handleDeleteNode = useCallback(() => {
    if (!selectedNode) return;
    setNodes((prev) => prev.filter((n) => n.id !== selectedNode.id));
    setEdges((prev) => prev.filter((e) => e.source !== selectedNode.id && e.target !== selectedNode.id));
    handleDeselectNode();
  }, [selectedNode, handleDeselectNode]);

  const handleStartConnect = useCallback((nodeId: string) => {
    if (connectingFrom === nodeId) {
      setConnectingFrom(null);
    } else {
      setConnectingFrom(nodeId);
    }
  }, [connectingFrom]);

  const handleEndConnect = useCallback((targetId: string) => {
    if (!connectingFrom || connectingFrom === targetId) {
      setConnectingFrom(null);
      return;
    }
    const exists = edges.some((e) => e.source === connectingFrom && e.target === targetId);
    if (!exists) {
      const newEdge: WorkflowEdge = {
        id: `e-${connectingFrom}-${targetId}`,
        source: connectingFrom,
        target: targetId,
        label: '',
      };
      setEdges((prev) => [...prev, newEdge]);
    }
    setConnectingFrom(null);
  }, [connectingFrom, edges]);

  const handleRemoveEdge = useCallback((edgeId: string) => {
    setEdges((prev) => prev.filter((e) => e.id !== edgeId));
  }, []);

  const handleValidate = useCallback(() => {
    const errors: string[] = [];
    if (nodes.length === 0) errors.push('Workflow has no nodes');
    const hasStart = nodes.some((n) => n.type === 'start');
    const hasEnd = nodes.some((n) => n.type === 'end');
    if (!hasStart) errors.push('Workflow is missing a Start node');
    if (!hasEnd) errors.push('Workflow is missing an End node');
    const incoming = new Map<string, number>();
    const outgoing = new Map<string, number>();
    nodes.forEach((n) => { incoming.set(n.id, 0); outgoing.set(n.id, 0); });
    edges.forEach((e) => {
      outgoing.set(e.source, (outgoing.get(e.source) || 0) + 1);
      incoming.set(e.target, (incoming.get(e.target) || 0) + 1);
    });
    nodes.forEach((n) => {
      if (n.type !== 'start' && (incoming.get(n.id) || 0) === 0) {
        errors.push(`Node "${n.label}" has no incoming connections`);
      }
      if (n.type !== 'end' && (outgoing.get(n.id) || 0) === 0) {
        errors.push(`Node "${n.label}" has no outgoing connections`);
      }
    });
    setValidationErrors(errors);
    if (onValidate) onValidate(nodes, edges);
    return errors.length === 0;
  }, [nodes, edges, onValidate]);

  const handleSave = useCallback(async () => {
    if (!handleValidate()) return;
    setIsSaving(true);
    try {
      if (onSave) {
        await Promise.resolve(onSave(nodes, edges));
      }
    } finally {
      setIsSaving(false);
    }
  }, [nodes, edges, onSave, handleValidate]);

  const handleRun = useCallback(async () => {
    handleValidate();
    await executeWorkflow(nodes, edges);
  }, [nodes, edges, executeWorkflow, handleValidate]);

  // Sync execution results to node statuses
  useEffect(() => {
    if (executionResults && executionResults.length > 0) {
      setNodes((prev) =>
        prev.map((node) => {
          const result = executionResults.find((r) => r.node_id === node.id);
          if (result) {
            return { ...node, status: result.status as WorkflowNode['status'] };
          }
          if (executingNodeId === node.id) {
            return { ...node, status: 'running' };
          }
          return node;
        })
      );
    }
  }, [executionResults, executingNodeId]);

  const handleZoomIn = useCallback(() => {
    setZoom((prev) => Math.min(prev + 10, 150));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoom((prev) => Math.max(prev - 10, 50));
  }, []);

  const handleZoomReset = useCallback(() => {
    setZoom(100);
  }, []);

  return (
    <div className="flex h-full flex-col rounded-lg border border-border bg-bg">
      {/* Workflow Management Bar */}
      <div className="flex items-center gap-3 border-b border-border px-4 py-2 bg-surface">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-text-muted" />
          <input
            type="text"
            value={currentWorkflowName}
            onChange={(e) => setCurrentWorkflowName(e.target.value)}
            className="border-none bg-transparent text-sm font-semibold text-text focus:outline-none focus:ring-1 focus:ring-accent rounded px-1 py-0.5 w-48"
            placeholder="Workflow name"
          />
        </div>
        <div className="h-4 w-px bg-border" />
        <div className="flex items-center gap-2">
          <FolderOpen className="h-4 w-4 text-text-muted" />
          <div className="relative">
            <select
              value={currentProjectId || ''}
              onChange={(e) => setCurrentProjectId(e.target.value || null)}
              style={{ colorScheme: 'dark' }}
              className="appearance-none border border-border bg-[#1a1a1a] text-xs text-[#ededed] focus:outline-none focus:ring-1 focus:ring-accent rounded px-2 py-1.5 pr-6 cursor-pointer hover:bg-[#222222]"
            >
              <option value="" style={{ background: '#1a1a1a', color: '#ededed' }}>No project</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id} style={{ background: '#1a1a1a', color: '#ededed' }}>{p.name}</option>
              ))}
            </select>
            <ChevronDown className="pointer-events-none absolute right-1.5 top-1/2 h-3 w-3 -translate-y-1/2 text-text-muted" />
          </div>
        </div>
        <div className="h-4 w-px bg-border" />
        <div className="relative">
          <select
            value={currentWorkflowId || ''}
            onChange={(e) => {
              if (e.target.value === '__new__') {
                newWorkflow();
              } else if (e.target.value) {
                loadWorkflow(e.target.value);
              }
            }}
            style={{ colorScheme: 'dark' }}
            className="appearance-none border border-border bg-[#1a1a1a] text-xs text-[#ededed] focus:outline-none focus:ring-1 focus:ring-accent rounded px-2 py-1.5 pr-6 cursor-pointer hover:bg-[#222222]"
          >
            <option value="__new__" style={{ background: '#1a1a1a', color: '#ededed' }}>+ New workflow</option>
            {savedWorkflows.map((w) => (
              <option key={w.id} value={w.id} style={{ background: '#1a1a1a', color: '#ededed' }}>{w.name}</option>
            ))}
          </select>
          <ChevronDown className="pointer-events-none absolute right-1.5 top-1/2 h-3 w-3 -translate-y-1/2 text-text-muted" />
        </div>
        <div className="flex-1" />
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm" onClick={() => saveCurrentWorkflow()} leftIcon={<Save className="h-3.5 w-3.5" />}>
            Save
          </Button>
          {currentWorkflowId && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => deleteWorkflow(currentWorkflowId)}
              leftIcon={<Trash2 className="h-3.5 w-3.5" />}
              className="text-red-400 hover:text-red-300"
            >
              Delete
            </Button>
          )}
        </div>
      </div>
      <Toolbar
        onAddNode={addNode}
        onValidate={handleValidate}
        onSave={handleSave}
        onRun={handleRun}
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onZoomReset={handleZoomReset}
        zoom={zoom}
        isSaving={isSaving}
        isRunning={isExecuting}
        validationErrors={validationErrors}
      />
      <div className="flex flex-1 overflow-hidden">
        <NodePalette onAddNode={addNode} />
        <Canvas
          ref={canvasRef}
          rows={rows}
          edges={edges}
          nodes={nodes}
          selectedNodeId={selectedNode?.id || null}
          connectingFrom={connectingFrom}
          zoom={zoom}
          executingNodeId={executingNodeId}
          executionResults={executionResults}
          onSelectNode={handleSelectNode}
          onStartConnect={handleStartConnect}
          onEndConnect={handleEndConnect}
          onRemoveEdge={handleRemoveEdge}
          onViewResult={setViewingResult}
        />
        {selectedNode && (
          <PropertiesPanel
            node={selectedNode}
            nodeTypes={NODE_TYPES}
            onUpdateNode={handleUpdateNode}
            onDeleteNode={handleDeleteNode}
            onClose={handleDeselectNode}
          />
        )}
      </div>

      {/* Full Output Modal */}
      {viewingResult && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setViewingResult(null)}>
          <div className="w-full max-w-2xl max-h-[80vh] rounded-xl border border-border bg-surface shadow-2xl overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between border-b border-border px-5 py-3">
              <div className="flex items-center gap-3">
                <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${getNodeTypeInfo(viewingResult.node_type as any).bgClass}`}>
                  <span className={getNodeTypeInfo(viewingResult.node_type as any).textClass}>
                    {getNodeTypeInfo(viewingResult.node_type as any).icon}
                  </span>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-text">{viewingResult.label}</h3>
                  <p className="text-xs text-text-muted">{viewingResult.node_type} node</p>
                </div>
              </div>
              <button onClick={() => setViewingResult(null)} className="rounded-lg p-1.5 hover:bg-surface-hover transition-colors">
                <X className="h-4 w-4 text-text-muted" />
              </button>
            </div>
            <div className="overflow-y-auto p-5 space-y-4" style={{ maxHeight: 'calc(80vh - 60px)' }}>
              {/* Status & Timing */}
              <div className="flex flex-wrap gap-3">
                <div className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${
                  viewingResult.status === 'completed' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
                }`}>
                  <span className={`h-1.5 w-1.5 rounded-full ${viewingResult.status === 'completed' ? 'bg-green-500' : 'bg-red-500'}`} />
                  {viewingResult.status === 'completed' ? 'Completed' : 'Failed'}
                </div>
                {viewingResult.duration_ms > 0 && (
                  <div className="flex items-center gap-1 rounded-full bg-blue-500/10 px-3 py-1 text-xs text-blue-400">
                    {viewingResult.duration_ms}ms
                  </div>
                )}
                {viewingResult.llm_model && (
                  <div className="flex items-center gap-1 rounded-full bg-purple-500/10 px-3 py-1 text-xs text-purple-400">
                    {viewingResult.llm_model}
                  </div>
                )}
                {viewingResult.tokens_used ? (
                  <div className="flex items-center gap-1 rounded-full bg-yellow-500/10 px-3 py-1 text-xs text-yellow-400">
                    {viewingResult.tokens_used} tokens
                  </div>
                ) : null}
              </div>

              {/* Error */}
              {viewingResult.error && (
                <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4">
                  <p className="text-xs font-medium text-red-400 mb-1">Error</p>
                  <p className="text-sm text-red-300 whitespace-pre-wrap">{viewingResult.error}</p>
                </div>
              )}

              {/* Output */}
              {viewingResult.output && Object.keys(viewingResult.output).length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-medium text-text-muted uppercase tracking-wider">Output</p>
                  <div className="space-y-2">
                    {Object.entries(viewingResult.output).map(([key, value]) => (
                      <div key={key} className="rounded-lg border border-border bg-bg p-3">
                        <p className="text-xs font-medium text-accent mb-1">{key}</p>
                        {typeof value === 'string' ? (
                          <p className="text-sm text-text whitespace-pre-wrap break-words">{value}</p>
                        ) : typeof value === 'object' && value !== null ? (
                          <pre className="text-sm text-text whitespace-pre-wrap break-words font-mono text-xs bg-black/30 rounded p-2 mt-1 overflow-x-auto">
                            {JSON.stringify(value, null, 2)}
                          </pre>
                        ) : (
                          <p className="text-sm text-text">{String(value)}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Raw Response */}
              {(viewingResult.output as any)?.raw_response && (
                <div className="space-y-2">
                  <p className="text-xs font-medium text-text-muted uppercase tracking-wider">Raw LLM Response</p>
                  <pre className="rounded-lg border border-border bg-bg p-3 text-xs text-text whitespace-pre-wrap break-words font-mono overflow-x-auto max-h-64 overflow-y-auto">
                    {(viewingResult.output as any).raw_response}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

interface ToolbarProps {
  onAddNode: (type: NodeType) => void;
  onValidate: () => void;
  onSave: () => void;
  onRun: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onZoomReset: () => void;
  zoom: number;
  isSaving: boolean;
  isRunning: boolean;
  validationErrors: string[];
}

function Toolbar({ onAddNode, onValidate, onSave, onRun, onZoomIn, onZoomOut, onZoomReset, zoom, isSaving, isRunning, validationErrors }: ToolbarProps) {
  const [showAddMenu, setShowAddMenu] = useState(false);

  return (
    <div className="flex items-center gap-2 border-b border-border px-4 py-2">
      <div className="relative">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowAddMenu(!showAddMenu)}
          leftIcon={<Plus className="h-4 w-4" />}
        >
          Add Node
        </Button>
        {showAddMenu && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setShowAddMenu(false)} />
            <div className="absolute left-0 top-full z-50 mt-1 w-48 rounded-lg border border-border bg-surface shadow-lg">
              <div className="p-1">
                {NODE_TYPES.map((nt) => (
                  <button
                    key={nt.type}
                    className={`flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-text hover:bg-surface-hover ${nt.textClass}`}
                    onClick={() => {
                      onAddNode(nt.type);
                      setShowAddMenu(false);
                    }}
                  >
                    {nt.icon}
                    {nt.label}
                  </button>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
      <Button variant="outline" size="sm" onClick={onValidate} leftIcon={<Link2 className="h-4 w-4" />}>
        Validate
      </Button>
      <Button variant="default" size="sm" onClick={onSave} isLoading={isSaving} leftIcon={<Save className="h-4 w-4" />}>
        Save
      </Button>
      <Button
        variant={isRunning ? 'destructive' : 'default'}
        size="sm"
        onClick={onRun}
        isLoading={isRunning}
        leftIcon={isRunning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
        className={isRunning ? '' : 'bg-green-600 hover:bg-green-700 text-white'}
      >
        {isRunning ? 'Running...' : 'Run'}
      </Button>
      {validationErrors.length > 0 && (
        <Badge variant="destructive" className="ml-2">
          {validationErrors.length} error{validationErrors.length > 1 ? 's' : ''}
        </Badge>
      )}
      <div className="flex-1" />
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="icon" onClick={onZoomOut} className="h-8 w-8">
          <ZoomOut className="h-4 w-4" />
        </Button>
        <button
          onClick={onZoomReset}
          className="min-w-[48px] rounded px-2 py-1 text-xs text-text-muted hover:bg-surface-hover"
        >
          {zoom}%
        </button>
        <Button variant="ghost" size="icon" onClick={onZoomIn} className="h-8 w-8">
          <ZoomIn className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" onClick={onZoomReset} className="h-8 w-8">
          <Maximize2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

interface NodePaletteProps {
  onAddNode: (type: NodeType) => void;
}

function NodePalette({ onAddNode }: NodePaletteProps) {
  return (
    <div className="w-56 flex-shrink-0 overflow-y-auto border-r border-border bg-surface">
      <div className="p-3">
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-text-muted">
          Node Palette
        </h3>
        <div className="space-y-1">
          {NODE_TYPES.map((nt) => (
            <button
              key={nt.type}
              onClick={() => onAddNode(nt.type)}
              className={`flex w-full items-center gap-2 rounded-md border border-transparent px-3 py-2 text-left text-sm transition-colors hover:border-border hover:bg-surface-hover ${nt.textClass}`}
            >
              <div className={`flex h-7 w-7 items-center justify-center rounded ${nt.bgClass}`}>
                {nt.icon}
              </div>
              <span className="font-medium text-text">{nt.label}</span>
              <GripVertical className="ml-auto h-3 w-3 text-text-muted opacity-0 group-hover:opacity-100" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

interface CanvasProps {
  rows: [number, WorkflowNode[]][];
  edges: WorkflowEdge[];
  nodes: WorkflowNode[];
  selectedNodeId: string | null;
  connectingFrom: string | null;
  zoom: number;
  executingNodeId: string | null;
  executionResults: Array<{
    node_id: string;
    status: string;
    output: Record<string, unknown>;
    duration_ms: number;
    error?: string;
    llm_model?: string;
    tokens_used?: number;
  }> | null;
  onSelectNode: (node: WorkflowNode) => void;
  onStartConnect: (nodeId: string) => void;
  onEndConnect: (nodeId: string) => void;
  onRemoveEdge: (edgeId: string) => void;
  onViewResult: (result: any) => void;
}

const Canvas = React.forwardRef<HTMLDivElement, CanvasProps>(
  (
    { rows, edges, nodes, selectedNodeId, connectingFrom, zoom, executingNodeId, executionResults, onSelectNode, onStartConnect, onEndConnect, onRemoveEdge, onViewResult },
    ref
  ) => {
    const nodeRefMap = useRef<Map<string, HTMLDivElement>>(new Map());

    const getNodeCenter = useCallback((nodeId: string) => {
      const el = nodeRefMap.current.get(nodeId);
      if (!el) return null;
      const rect = el.getBoundingClientRect();
      const parent = el.closest('[data-canvas]');
      if (!parent) return null;
      const parentRect = parent.getBoundingClientRect();
      return {
        x: rect.left - parentRect.left + rect.width / 2,
        y: rect.top - parentRect.top + rect.height / 2,
        top: rect.top - parentRect.top,
        bottom: rect.top - parentRect.top + rect.height,
        height: rect.height,
      };
    }, []);

    return (
      <div
        ref={ref}
        data-canvas
        className="flex-1 overflow-auto bg-bg"
        style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'top left' }}
      >
        <div className="relative min-h-full min-w-full p-8">
          {rows.map(([rowIndex, rowNodes], ri) => (
            <div key={rowIndex} className="relative mb-2">
              <div className="flex items-start justify-center gap-6">
                {rowNodes.map((node) => {
                  const typeInfo = getNodeTypeInfo(node.type);
                  const isExecuting = executingNodeId === node.id;
                  const status = isExecuting && node.status !== 'completed' && node.status !== 'failed'
                    ? STATUS_CONFIG.running
                    : STATUS_CONFIG[node.status];
                  const isSelected = selectedNodeId === node.id;
                  const isConnectingSource = connectingFrom === node.id;
                  const isConnectingMode = connectingFrom !== null;
                  const nodeResult = executionResults?.find((r) => r.node_id === node.id);
                  const nodeError = nodeResult?.error || (nodeResult?.status === 'failed' ? (nodeResult?.output as any)?.raw_response || 'Execution failed' : null);

                  return (
                    <div key={node.id} className="relative" ref={(el) => { if (el) nodeRefMap.current.set(node.id, el); }}>
                      <div
                        onClick={() => {
                          if (isConnectingMode && connectingFrom !== node.id) {
                            onEndConnect(node.id);
                          } else {
                            onSelectNode(node);
                          }
                        }}
                        className={`group relative w-48 cursor-pointer rounded-lg border-2 p-3 shadow-sm transition-all hover:shadow-md ${
                          isSelected
                            ? `ring-2 ring-offset-2 ring-offset-bg ${typeInfo.borderClass} border-current ${typeInfo.textClass}`
                            : `${typeInfo.borderClass} ${typeInfo.bgClass}`
                        } ${isConnectingSource ? 'ring-2 ring-accent ring-offset-2 ring-offset-bg' : ''} ${isConnectingMode && !isConnectingSource ? 'hover:ring-2 hover:ring-accent' : ''} ${isExecuting && node.status !== 'completed' && node.status !== 'failed' ? 'ring-2 ring-blue-500 ring-offset-2 ring-offset-bg animate-pulse' : ''}`}
                      >
                        <div className="flex items-center gap-2">
                          <div className={`flex h-6 w-6 items-center justify-center rounded ${typeInfo.bgClass} ${typeInfo.textClass}`}>
                            {typeInfo.icon}
                          </div>
                          <span className="text-sm font-medium text-text truncate">{node.label}</span>
                        </div>
                        <div className="mt-2 flex items-center justify-between">
                          <div className="flex items-center gap-1.5">
                            <span className={`h-1.5 w-1.5 rounded-full ${status.dot}`} />
                            <span className={`text-xs ${status.text}`}>{status.label}</span>
                          </div>
                          <div className="flex gap-1">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onStartConnect(node.id);
                              }}
                              className="opacity-0 group-hover:opacity-100 h-5 w-5 flex items-center justify-center rounded bg-surface hover:bg-surface-hover transition-opacity"
                              title="Connect to another node"
                            >
                              <Link2 className="h-3 w-3" />
                            </button>
                          </div>
                        </div>
                        {nodeError && node.status === 'failed' && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onViewResult(nodeResult);
                            }}
                            className="mt-2 w-full text-left rounded bg-red-500/10 border border-red-500/20 px-2 py-1 hover:bg-red-500/20 transition-colors cursor-pointer"
                          >
                            <p className="text-[10px] text-red-400 truncate" title={nodeError}>{nodeError}</p>
                          </button>
                        )}
                        {nodeResult && nodeResult.status === 'completed' && node.type !== 'start' && node.type !== 'end' && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onViewResult(nodeResult);
                            }}
                            className="mt-2 w-full text-left space-y-1 cursor-pointer hover:opacity-80 transition-opacity"
                          >
                            <div className="rounded bg-green-500/10 border border-green-500/20 px-2 py-1">
                              <p className="text-[10px] text-green-400">
                                {nodeResult.duration_ms}ms
                                {nodeResult.llm_model ? ` · ${nodeResult.llm_model}` : ''}
                              </p>
                            </div>
                            {nodeResult.output && Object.keys(nodeResult.output).length > 0 && (
                              <div className="rounded bg-black/40 border border-border px-2 py-1.5 max-h-24 overflow-y-auto">
                                {Object.entries(nodeResult.output).filter(([k]) => k !== 'raw_response').slice(0, 4).map(([key, value]) => (
                                  <div key={key} className="text-[10px] leading-relaxed">
                                    <span className="text-text-muted">{key}: </span>
                                    <span className="text-text break-words">
                                      {typeof value === 'string' ? (value.length > 80 ? value.slice(0, 80) + '...' : value) :
                                       typeof value === 'object' ? JSON.stringify(value).slice(0, 80) :
                                       String(value)}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
              {ri < rows.length - 1 && (
                <div className="flex justify-center py-2">
                  <div className="flex flex-col items-center">
                    <ArrowDown className="h-4 w-4 text-text-muted" />
                    <div className="w-px h-2 bg-border" />
                  </div>
                </div>
              )}
            </div>
          ))}
          <EdgeOverlay edges={edges} nodes={nodes} getNodeCenter={getNodeCenter} onRemoveEdge={onRemoveEdge} />
        </div>
      </div>
    );
  }
);
Canvas.displayName = 'Canvas';

interface EdgeOverlayProps {
  edges: WorkflowEdge[];
  nodes: WorkflowNode[];
  getNodeCenter: (nodeId: string) => { x: number; y: number; top: number; bottom: number; height: number } | null;
  onRemoveEdge: (edgeId: string) => void;
}

function EdgeOverlay({ edges, nodes, getNodeCenter, onRemoveEdge }: EdgeOverlayProps) {
  const [lines, setLines] = useState<{ id: string; x1: number; y1: number; x2: number; y2: number; midX: number; midY: number; label: string }[]>([]);

  useEffect(() => {
    const timer = setTimeout(() => {
      const computed = edges
        .map((edge) => {
          const source = getNodeCenter(edge.source);
          const target = getNodeCenter(edge.target);
          if (!source || !target) return null;
          const sourceNode = nodes.find((n) => n.id === edge.source);
          const isAbove = sourceNode && target.y > source.y;
          return {
            id: edge.id,
            x1: source.x,
            y1: isAbove ? source.bottom : source.top,
            x2: target.x,
            y2: isAbove ? target.top : target.bottom,
            midX: (source.x + target.x) / 2,
            midY: ((isAbove ? source.bottom : source.top) + (isAbove ? target.top : target.bottom)) / 2,
            label: edge.label,
          };
        })
        .filter(Boolean) as typeof lines;
      setLines(computed);
    }, 50);
    return () => clearTimeout(timer);
  }, [edges, nodes, getNodeCenter]);

  return (
    <svg className="pointer-events-none absolute inset-0 h-full w-full" style={{ zIndex: 0 }}>
      {lines.map((line) => {
        const midY = (line.y1 + line.y2) / 2;
        const pathD = `M ${line.x1} ${line.y1} C ${line.x1} ${midY}, ${line.x2} ${midY}, ${line.x2} ${line.y2}`;
        return (
          <g key={line.id}>
            <path d={pathD} fill="none" stroke="hsl(var(--border))" strokeWidth="2" />
            <polygon
              points={`${line.x2 - 4},${line.y2 - 2} ${line.x2 + 4},${line.y2 - 2} ${line.x2},${line.y2 + 4}`}
              fill="hsl(var(--border))"
            />
            <foreignObject x={line.midX - 10} y={midY - 10} width="20" height="20" className="pointer-events-auto">
              <button
                onClick={() => onRemoveEdge(line.id)}
                className="flex h-5 w-5 items-center justify-center rounded-full bg-surface text-text-muted opacity-0 hover:bg-danger hover:text-danger-text hover:opacity-100 transition-opacity"
              >
                <X className="h-3 w-3" />
              </button>
            </foreignObject>
          </g>
        );
      })}
    </svg>
  );
}

interface PropertiesPanelProps {
  node: WorkflowNode;
  nodeTypes: NodeTypeInfo[];
  onUpdateNode: (updates: Partial<WorkflowNode>) => void;
  onDeleteNode: () => void;
  onClose: () => void;
}

function PropertiesPanel({ node, nodeTypes, onUpdateNode, onDeleteNode, onClose }: PropertiesPanelProps) {
  const typeInfo = getNodeTypeInfo(node.type);

  return (
    <div className="w-72 flex-shrink-0 overflow-y-auto border-l border-border bg-surface">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <Settings className="h-4 w-4 text-text-muted" />
          <h3 className="text-sm font-semibold text-text">Properties</h3>
        </div>
        <button onClick={onClose} className="rounded p-1 hover:bg-surface-hover">
          <X className="h-4 w-4 text-text-muted" />
        </button>
      </div>
      <div className="space-y-4 p-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-text-muted">Type</label>
          <div className={`flex items-center gap-2 rounded-md border px-3 py-2 ${typeInfo.borderClass} ${typeInfo.bgClass}`}>
            <span className={typeInfo.textClass}>{typeInfo.icon}</span>
            <span className="text-sm font-medium text-text">{typeInfo.label}</span>
          </div>
        </div>
        <Input
          label="Label"
          value={node.label}
          onChange={(e) => onUpdateNode({ label: e.target.value })}
          placeholder="Node label"
        />
        <div>
          <label className="mb-1 block text-xs font-medium text-text-muted">Status</label>
          <div className="flex flex-wrap gap-1">
            {Object.entries(STATUS_CONFIG).map(([key, config]) => (
              <button
                key={key}
                onClick={() => onUpdateNode({ status: key as WorkflowNode['status'] })}
                className={`flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs transition-colors ${
                  node.status === key
                    ? `${config.bg} ${config.text} border-current`
                    : 'border-border text-text-muted hover:bg-surface-hover'
                }`}
              >
                <span className={`h-1.5 w-1.5 rounded-full ${config.dot}`} />
                {config.label}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-text-muted">Description</label>
          <Textarea
            value={(node.data.description as string) || ''}
            onChange={(e) => onUpdateNode({ data: { ...node.data, description: e.target.value } })}
            placeholder="Describe this node..."
            rows={3}
          />
        </div>
        {node.type === 'agent' && (
          <Input
            label="Role"
            value={(node.data.role as string) || ''}
            onChange={(e) => onUpdateNode({ data: { ...node.data, role: e.target.value } })}
            placeholder="Agent role"
          />
        )}
        {node.type === 'planner' && (
          <Input
            label="Model"
            value={(node.data.model as string) || ''}
            onChange={(e) => onUpdateNode({ data: { ...node.data, model: e.target.value } })}
            placeholder="e.g. gpt-4"
          />
        )}
        {node.type === 'decision' && (
          <Input
            label="Condition"
            value={(node.data.condition as string) || ''}
            onChange={(e) => onUpdateNode({ data: { ...node.data, condition: e.target.value } })}
            placeholder="e.g. output.score > 0.8"
          />
        )}
        {node.type === 'tool' && (
          <Input
            label="Tool Name"
            value={(node.data.tool as string) || ''}
            onChange={(e) => onUpdateNode({ data: { ...node.data, tool: e.target.value } })}
            placeholder="Tool to invoke"
          />
        )}
        <div className="border-t border-border pt-4">
          <p className="mb-2 text-xs text-text-muted">Node ID: {node.id}</p>
          <p className="text-xs text-text-muted">
            Position: ({node.position.x}, {node.position.y})
          </p>
        </div>
        <Button
          variant="destructive"
          size="sm"
          onClick={onDeleteNode}
          leftIcon={<Trash2 className="h-4 w-4" />}
          className="w-full"
        >
          Delete Node
        </Button>
      </div>
    </div>
  );
}