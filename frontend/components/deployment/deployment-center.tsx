"use client";

import * as React from "react";
import {
  Rocket,
  FolderOpen,
  Download,
  Shield,
  FileCode,
  GitBranch,
  Server,
  Activity,
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Copy,
  Box,
  Layers,
  Database,
  Globe,
  Terminal,
  BarChart3,
} from "lucide-react";
import Link from "next/link";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useDeploymentStore } from "@/stores/deployment-store";
import type {
  SecurityIssue,
  SecuritySeverity,
  ScoreItem,
  K8sResource,
  DeploymentPlan,
  InfrastructureDiagram,
} from "@/types/deployment";

type TabValue = "overview" | "docker" | "cicd" | "kubernetes" | "security" | "report";

const severityConfig: Record<SecuritySeverity, { label: string; variant: "destructive" | "warning" | "default" | "success" }> = {
  critical: { label: "Critical", variant: "destructive" },
  high: { label: "High", variant: "destructive" },
  medium: { label: "Medium", variant: "warning" },
  low: { label: "Low", variant: "default" },
  info: { label: "Info", variant: "success" },
};

const componentIcons: Record<string, React.ReactNode> = {
  database: <Database className="h-5 w-5" />,
  cache: <Server className="h-5 w-5" />,
  web: <Globe className="h-5 w-5" />,
  api: <Terminal className="h-5 w-5" />,
  queue: <Activity className="h-5 w-5" />,
  default: <Box className="h-5 w-5" />,
};

function getGradeColor(grade: string): string {
  if (grade === "A" || grade === "A+") return "text-success";
  if (grade === "B" || grade === "B+") return "text-accent";
  if (grade === "C") return "text-warning";
  return "text-danger";
}

function getScoreRingColor(score: number): string {
  if (score >= 80) return "stroke-success";
  if (score >= 60) return "stroke-accent";
  if (score >= 40) return "stroke-warning";
  return "stroke-danger";
}

function ScoreCircle({ score, grade }: { score: number; grade: string }) {
  const circumference = 2 * Math.PI * 45;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="relative flex items-center justify-center">
      <svg className="h-36 w-36 -rotate-90" viewBox="0 0 100 100">
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          className="text-border"
        />
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className={`${getScoreRingColor(score)} transition-all duration-1000`}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-3xl font-bold text-text">{score}</span>
        <span className={`text-sm font-semibold ${getGradeColor(grade)}`}>
          Grade {grade}
        </span>
      </div>
    </div>
  );
}

function CodeBlock({ content, filename }: { content: string; filename?: string }) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-lg border border-border bg-surface">
      {filename && (
        <div className="flex items-center justify-between border-b border-border px-4 py-2">
          <span className="flex items-center gap-2 text-sm font-medium text-text">
            <FileCode className="h-4 w-4 text-text-muted" />
            {filename}
          </span>
          <Button variant="ghost" size="sm" onClick={handleCopy}>
            <Copy className="h-3.5 w-3.5 mr-1" />
            {copied ? "Copied!" : "Copy"}
          </Button>
        </div>
      )}
      <pre className="overflow-x-auto p-4 text-sm font-mono text-text">
        <code>{content}</code>
      </pre>
    </div>
  );
}

function OverviewSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid gap-6 md:grid-cols-3">
        <Skeleton className="h-44" />
        <Skeleton className="h-44" />
        <Skeleton className="h-44" />
      </div>
      <Skeleton className="h-64" />
    </div>
  );
}

function DeploymentCenter() {
  const [activeTab, setActiveTab] = React.useState<TabValue>("overview");
  const [repoPath, setRepoPath] = React.useState("");
  const [selectedFile, setSelectedFile] = React.useState<string | null>(null);
  const [repositories, setRepositories] = React.useState<Array<{id: string; name: string; local_path?: string; file_count?: number; languages?: Array<{name: string}>}>>([]);
  const [selectedRepoId, setSelectedRepoId] = React.useState<string>("");
  const [isLoadingRepos, setIsLoadingRepos] = React.useState(true);

  const {
    currentTask,
    isLoading,
    error,
    analysis,
    security,
    score,
    dockerfile,
    compose,
    composeDev,
    githubActions,
    kubernetes,
    analyze,
    clearError,
  } = useDeploymentStore();

  // Fetch repositories on mount
  React.useEffect(() => {
    const fetchRepos = async () => {
      setIsLoadingRepos(true);
      try {
        const { apiClient } = await import("@/services/api");
        const res = await apiClient.get("/repositories");
        const repos = res.data?.data || [];
        setRepositories(repos);
        // Auto-select first repo if available and auto-fill path
        if (repos.length > 0 && !selectedRepoId) {
          const firstRepo = repos[0];
          setSelectedRepoId(firstRepo.id);
          if (firstRepo.local_path) {
            setRepoPath(firstRepo.local_path);
          }
        }
      } catch (err) {
        console.error("Failed to fetch repositories:", err);
      } finally {
        setIsLoadingRepos(false);
      }
    };
    fetchRepos();
  }, []);

  const handleRepoSelect = (repoId: string) => {
    setSelectedRepoId(repoId);
    const repo = repositories.find(r => r.id === repoId);
    if (repo?.local_path) {
      setRepoPath(repo.local_path);
    } else {
      setRepoPath("");
    }
  };

  const handleAnalyze = () => {
    if (!selectedRepoId && !repoPath.trim()) {
      return;
    }
    const pathToUse = repoPath.trim() || ".";
    analyze(selectedRepoId || "manual", pathToUse);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && repoPath.trim()) {
      handleAnalyze();
    }
  };

  const hasData = currentTask !== null;
  const selectedRepo = repositories.find(r => r.id === selectedRepoId);

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10">
            <Rocket className="h-5 w-5 text-accent" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-text">Deployment Center</h1>
            <p className="text-sm text-text-muted">
              Analyze, configure, and deploy your applications
            </p>
          </div>
        </div>
        <Button
          onClick={handleAnalyze}
          disabled={(!selectedRepoId && !repoPath.trim()) || isLoading}
          isLoading={isLoading}
          leftIcon={!isLoading ? <Rocket className="h-4 w-4" /> : undefined}
        >
          {isLoading ? "Analyzing..." : selectedRepo ? `Analyze ${selectedRepo.name}` : "Analyze"}
        </Button>
      </div>

      {/* Repository Selection */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col gap-4">
            {/* Repository Selector - Primary */}
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-text">
                Select Repository
              </label>
              {isLoadingRepos ? (
                <div className="flex h-10 items-center gap-2 rounded-md border border-border bg-surface px-3">
                  <Skeleton className="h-4 w-4" />
                  <Skeleton className="h-4 w-32" />
                </div>
              ) : repositories.length > 0 ? (
                <div className="flex gap-3">
                  <select
                    value={selectedRepoId}
                    onChange={(e) => handleRepoSelect(e.target.value)}
                    className="flex-1 rounded-md border border-border bg-surface px-3 py-2 text-sm text-text focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                  >
                    <option value="">Choose a repository...</option>
                    {repositories.map((repo) => (
                      <option key={repo.id} value={repo.id}>
                        {repo.name} {repo.local_path ? `(${repo.local_path})` : ''}
                      </option>
                    ))}
                  </select>
                  {selectedRepo && (
                    <div className="flex items-center gap-2 text-sm text-text-muted">
                      {selectedRepo.file_count && (
                        <Badge variant="secondary">{selectedRepo.file_count} files</Badge>
                      )}
                      {selectedRepo.languages && selectedRepo.languages.length > 0 && (
                        <Badge variant="outline">{selectedRepo.languages[0]?.name || 'Unknown'}</Badge>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center gap-2 rounded-md border border-border bg-surface px-3 py-2 text-sm text-text-muted">
                  <GitBranch className="h-4 w-4" />
                  <span>No repositories imported yet.</span>
                  <Link href="/repositories" className="ml-2 text-accent hover:underline">
                    Import Repository
                  </Link>
                </div>
              )}
            </div>

            {/* Path Input - Secondary (auto-filled from repo) */}
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-text">
                Project Path
                <span className="ml-2 text-xs text-text-muted">(auto-filled from repository)</span>
              </label>
              <Input
                placeholder="Enter repository path (e.g., /path/to/project)"
                value={repoPath}
                onChange={(e) => setRepoPath(e.target.value)}
                onKeyDown={handleKeyDown}
                leftIcon={<FolderOpen className="h-4 w-4" />}
                disabled={!selectedRepoId}
                className={!selectedRepoId ? "opacity-50" : ""}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error State */}
      {error && (
        <Card className="border-danger/50 bg-danger/5">
          <CardContent className="flex items-center gap-3 p-4">
            <AlertTriangle className="h-5 w-5 text-danger flex-shrink-0" />
            <p className="text-sm text-danger flex-1">{error}</p>
            <Button variant="ghost" size="sm" onClick={clearError}>
              Dismiss
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Loading State */}
      {isLoading && !hasData && (
        <OverviewSkeleton />
      )}

      {/* Main Content Tabs */}
      {hasData && (
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabValue)}>
          <TabsList className="mb-6 flex-wrap">
            <TabsTrigger value="overview" className="gap-1.5">
              <Layers className="h-3.5 w-3.5" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="docker" className="gap-1.5">
              <Box className="h-3.5 w-3.5" />
              Docker
            </TabsTrigger>
            <TabsTrigger value="cicd" className="gap-1.5">
              <GitBranch className="h-3.5 w-3.5" />
              CI/CD
            </TabsTrigger>
            <TabsTrigger value="kubernetes" className="gap-1.5">
              <Server className="h-3.5 w-3.5" />
              Kubernetes
            </TabsTrigger>
            <TabsTrigger value="security" className="gap-1.5">
              <Shield className="h-3.5 w-3.5" />
              Security
            </TabsTrigger>
            <TabsTrigger value="report" className="gap-1.5">
              <BarChart3 className="h-3.5 w-3.5" />
              Report
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Score and Analysis Summary */}
            <div className="grid gap-6 md:grid-cols-3">
              {/* Production Score */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm text-text-muted">
                    Production Score
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex justify-center pt-2">
                  {score ? (
                    <ScoreCircle score={score.overall_score} grade={score.grade} />
                  ) : (
                    <div className="flex h-36 items-center justify-center text-text-muted">
                      No score available
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Infrastructure */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm text-text-muted">
                    Infrastructure Detected
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {analysis ? (
                    <div className="space-y-3">
                      <div className="text-2xl font-bold text-text">
                        {analysis.components.length}
                      </div>
                      <div className="space-y-1.5">
                        {analysis.components.slice(0, 4).map((comp, idx) => (
                          <div
                            key={`${comp.type}-${idx}`}
                            className="flex items-center gap-2 text-sm text-text-muted"
                          >
                            <ChevronRight className="h-3 w-3" />
                            {comp.name}
                          </div>
                        ))}
                        {analysis.components.length > 4 && (
                          <div className="text-xs text-text-muted">
                            +{analysis.components.length - 4} more
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="flex h-24 items-center justify-center text-text-muted">
                      No analysis data
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Quick Stats */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm text-text-muted">
                    Quick Stats
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-text-muted">Project Type</span>
                      <Badge variant="secondary">{analysis?.project_type || "—"}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-text-muted">Strategy</span>
                      <Badge variant="secondary">{analysis?.strategy || "—"}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-text-muted">Docker</span>
                      {analysis?.docker_present ? (
                        <CheckCircle2 className="h-4 w-4 text-success" />
                      ) : (
                        <AlertTriangle className="h-4 w-4 text-warning" />
                      )}
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-text-muted">CI/CD</span>
                      {analysis?.ci_cd_present ? (
                        <CheckCircle2 className="h-4 w-4 text-success" />
                      ) : (
                        <AlertTriangle className="h-4 w-4 text-warning" />
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Infrastructure Components */}
            {analysis && analysis.components.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">
                    Infrastructure Components ({analysis.components.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {analysis.components.map((comp, idx) => (
                      <Card key={`${comp.type}-${idx}`} className="bg-surface-active">
                        <CardContent className="p-4">
                          <div className="flex items-start gap-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10 text-accent">
                              {componentIcons[comp.type] || componentIcons.default}
                            </div>
                            <div className="flex-1 min-w-0">
                              <h4 className="text-sm font-medium text-text truncate">
                                {comp.name}
                              </h4>
                              <p className="text-xs text-text-muted">{comp.type}</p>
                              {comp.version && (
                                <p className="mt-1 text-xs text-text-muted">
                                  v{comp.version}
                                </p>
                              )}
                              {comp.port && (
                                <p className="text-xs text-text-muted">
                                  Port: {comp.port}
                                </p>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Score Dimensions */}
            {score && score.dimensions.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Score Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {score.dimensions.map((dim: ScoreItem) => (
                      <div key={dim.dimension} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-text">
                            {dim.dimension}
                          </span>
                          <span className="text-sm text-text-muted">
                            {dim.score}/{100} ({dim.weight}%)
                          </span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-surface-hover">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              dim.score >= 80
                                ? "bg-success"
                                : dim.score >= 60
                                ? "bg-accent"
                                : dim.score >= 40
                                ? "bg-warning"
                                : "bg-danger"
                            }`}
                            style={{ width: `${dim.score}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Docker Tab */}
          <TabsContent value="docker" className="space-y-6">
            {/* Dockerfile */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base">Dockerfile</CardTitle>
                    <CardDescription>
                      {dockerfile
                        ? `Base image: ${dockerfile.base_image} • Estimated size: ${dockerfile.size_estimate}`
                        : "No Dockerfile generated"}
                    </CardDescription>
                  </div>
                  {dockerfile && (
                    <Button variant="outline" size="sm" leftIcon={<Download className="h-4 w-4" />}>
                      Download
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {dockerfile ? (
                  <div className="space-y-4">
                    <CodeBlock content={dockerfile.content} filename="Dockerfile" />
                    {dockerfile.stages.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {dockerfile.stages.map((stage) => (
                          <Badge key={stage} variant="secondary">
                            {stage}
                          </Badge>
                        ))}
                      </div>
                    )}
                    {dockerfile.security_notes.length > 0 && (
                      <div className="rounded-lg border border-warning/50 bg-warning/5 p-3">
                        <h4 className="mb-2 text-sm font-medium text-warning">
                          Security Notes
                        </h4>
                        <ul className="space-y-1">
                          {dockerfile.security_notes.map((note, idx) => (
                            <li key={idx} className="text-xs text-text-muted">
                              • {note}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <Box className="mb-4 h-12 w-12 text-text-muted" />
                    <p className="text-sm text-text-muted">
                      Run analysis to generate Dockerfile
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Docker Compose */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base">Docker Compose</CardTitle>
                    <CardDescription>
                      {compose
                        ? `${compose.services_count} services • ${compose.volumes_count} volumes • ${compose.networks_count} networks`
                        : "No Docker Compose generated"}
                    </CardDescription>
                  </div>
                  {compose && (
                    <Button variant="outline" size="sm" leftIcon={<Download className="h-4 w-4" />}>
                      Download
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {compose ? (
                  <div className="space-y-4">
                    <CodeBlock content={compose.content} filename="docker-compose.yml" />
                    {compose.notes.length > 0 && (
                      <div className="space-y-1">
                        {compose.notes.map((note, idx) => (
                          <p key={idx} className="text-xs text-text-muted">
                            • {note}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <Box className="mb-4 h-12 w-12 text-text-muted" />
                    <p className="text-sm text-text-muted">
                      Run analysis to generate Docker Compose
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Dev Compose */}
            {composeDev && (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-base">Development Compose</CardTitle>
                      <CardDescription>
                        {composeDev.variant} • {composeDev.services_count} services
                      </CardDescription>
                    </div>
                    <Button variant="outline" size="sm" leftIcon={<Download className="h-4 w-4" />}>
                      Download
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <CodeBlock content={composeDev.content} filename="docker-compose.dev.yml" />
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* CI/CD Tab */}
          <TabsContent value="cicd" className="space-y-6">
            {githubActions && githubActions.workflows.length > 0 ? (
              githubActions.workflows.map((workflow) => (
                <Card key={workflow.filename}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-base">{workflow.type}</CardTitle>
                        <CardDescription>{workflow.filename}</CardDescription>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" leftIcon={<Copy className="h-4 w-4" />}>
                          Copy
                        </Button>
                        <Button variant="outline" size="sm" leftIcon={<Download className="h-4 w-4" />}>
                          Download
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <CodeBlock content={workflow.content} filename={workflow.filename} />
                  </CardContent>
                </Card>
              ))
            ) : (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                  <GitBranch className="mb-4 h-12 w-12 text-text-muted" />
                  <h3 className="mb-2 text-lg font-semibold text-text">
                    No CI/CD Workflows
                  </h3>
                  <p className="max-w-sm text-sm text-text-muted">
                    Run analysis to generate GitHub Actions workflows for automated
                    building and deployment.
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Kubernetes Tab */}
          <TabsContent value="kubernetes" className="space-y-6">
            {kubernetes && kubernetes.resources.length > 0 ? (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">
                      Kubernetes Resources ({kubernetes.total_resources})
                    </CardTitle>
                    <CardDescription>
                      Namespace: {kubernetes.namespace}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {kubernetes.resources.map((resource: K8sResource, idx: number) => (
                        <Badge
                          key={`${resource.resource_type}-${idx}`}
                          variant="outline"
                          className="cursor-pointer"
                          onClick={() => setSelectedFile(resource.name)}
                        >
                          {resource.resource_type}: {resource.name}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Selected Resource Content */}
                {selectedFile && (() => {
                  const resource = kubernetes.resources.find(
                    (r: K8sResource) => r.name === selectedFile
                  );
                  if (!resource) return null;
                  return (
                    <Card>
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle className="text-base">
                              {resource.resource_type}: {resource.name}
                            </CardTitle>
                            <CardDescription>
                              Namespace: {resource.namespace}
                            </CardDescription>
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            leftIcon={<Download className="h-4 w-4" />}
                          >
                            Download
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <CodeBlock
                          content={resource.content}
                          filename={`${resource.resource_type.toLowerCase()}-${resource.name}.yaml`}
                        />
                      </CardContent>
                    </Card>
                  );
                })()}

                {/* All Resources */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">All Resources</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {kubernetes.resources.map((resource: K8sResource, idx: number) => (
                        <div
                          key={`${resource.resource_type}-${idx}`}
                          className="rounded-lg border border-border p-4"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Badge variant="secondary">{resource.resource_type}</Badge>
                              <span className="text-sm font-medium text-text">
                                {resource.name}
                              </span>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() =>
                                setSelectedFile(
                                  selectedFile === resource.name ? null : resource.name
                                )
                              }
                            >
                              {selectedFile === resource.name ? "Collapse" : "Expand"}
                            </Button>
                          </div>
                          {selectedFile === resource.name && (
                            <pre className="mt-3 overflow-x-auto rounded-md bg-surface p-3 text-xs font-mono text-text">
                              {resource.content}
                            </pre>
                          )}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                  <Server className="mb-4 h-12 w-12 text-text-muted" />
                  <h3 className="mb-2 text-lg font-semibold text-text">
                    No Kubernetes Manifests
                  </h3>
                  <p className="max-w-sm text-sm text-text-muted">
                    Run analysis to generate Kubernetes deployment, service, and
                    configuration manifests.
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Security Tab */}
          <TabsContent value="security" className="space-y-6">
            {security ? (
              <>
                {/* Security Summary */}
                <div className="grid gap-4 sm:grid-cols-4">
                  <Card>
                    <CardContent className="p-4 text-center">
                      <div className="text-2xl font-bold text-danger">
                        {security.critical_count}
                      </div>
                      <p className="text-xs text-text-muted">Critical</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4 text-center">
                      <div className="text-2xl font-bold text-warning">
                        {security.high_count}
                      </div>
                      <p className="text-xs text-text-muted">High</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4 text-center">
                      <div className="text-2xl font-bold text-accent">
                        {security.medium_count}
                      </div>
                      <p className="text-xs text-text-muted">Medium</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4 text-center">
                      <div className="text-2xl font-bold text-text-muted">
                        {security.low_count}
                      </div>
                      <p className="text-xs text-text-muted">Low</p>
                    </CardContent>
                  </Card>
                </div>

                {/* Security Score */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Security Score</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-6">
                      <ScoreCircle score={security.score} grade={security.score >= 80 ? "A" : security.score >= 60 ? "B" : security.score >= 40 ? "C" : "F"} />
                      <div className="flex-1 space-y-2">
                        <p className="text-sm text-text-muted">
                          {security.total_issues} issues found across{" "}
                          {security.categories_checked.length} categories
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {security.categories_checked.map((cat) => (
                            <Badge key={cat} variant="outline" className="capitalize">
                              {cat}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Security Issues List */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">
                      Security Issues ({security.total_issues})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {security.issues.map((issue: SecurityIssue, idx: number) => (
                        <div
                          key={idx}
                          className="rounded-lg border border-border p-4 transition-colors hover:bg-surface-active"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <Badge variant={severityConfig[issue.severity].variant}>
                                  {severityConfig[issue.severity].label}
                                </Badge>
                                <Badge variant="outline" className="capitalize">
                                  {issue.category}
                                </Badge>
                              </div>
                              <h4 className="text-sm font-medium text-text">
                                {issue.title}
                              </h4>
                              <p className="mt-1 text-xs text-text-muted">
                                {issue.description}
                              </p>
                              {issue.file_path && (
                                <p className="mt-2 font-mono text-xs text-text-muted">
                                  {issue.file_path}
                                  {issue.line_number ? `:${issue.line_number}` : ""}
                                </p>
                              )}
                              {issue.recommendation && (
                                <p className="mt-2 text-xs text-accent">
                                  Recommendation: {issue.recommendation}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                  <Shield className="mb-4 h-12 w-12 text-text-muted" />
                  <h3 className="mb-2 text-lg font-semibold text-text">
                    No Security Analysis
                  </h3>
                  <p className="max-w-sm text-sm text-text-muted">
                    Run analysis to perform security validation and detect potential
                    vulnerabilities.
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Report Tab */}
          <TabsContent value="report" className="space-y-6">
            {currentTask?.artifacts.report ? (
              (() => {
                const report = currentTask.artifacts.report as {
                  project_name: string;
                  timestamp: string;
                  score: number;
                  sections: Array<{ title: string; content: string; severity: string; order?: number }>;
                  plan: DeploymentPlan;
                  diagram: InfrastructureDiagram;
                };
                return (
                  <>
                    {/* Report Header */}
                    <Card>
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle className="text-lg">{report.project_name}</CardTitle>
                            <CardDescription>
                              Generated: {new Date(report.timestamp).toLocaleString()}
                            </CardDescription>
                          </div>
                          <div className="flex gap-2">
                            <Button variant="outline" size="sm" leftIcon={<Download className="h-4 w-4" />}>
                              Export PDF
                            </Button>
                            <Button variant="outline" size="sm" leftIcon={<Copy className="h-4 w-4" />}>
                              Copy Report
                            </Button>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center gap-4">
                          <div className="text-3xl font-bold text-text">
                            {report.score}/100
                          </div>
                          <div className="text-sm text-text-muted">
                            Overall Deployment Score
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Deployment Plan */}
                    {report.plan && (
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-base">Deployment Plan</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                            <div className="space-y-2">
                              <h4 className="text-sm font-medium text-text-muted">Strategy</h4>
                              <Badge variant="secondary" className="capitalize">
                                {report.plan.strategy}
                              </Badge>
                            </div>
                            <div className="space-y-2">
                              <h4 className="text-sm font-medium text-text-muted">Containers</h4>
                              <div className="space-y-1">
                                {report.plan.containers.map((container) => (
                                  <p key={container.name} className="text-sm text-text">
                                    {container.name} ({container.image})
                                  </p>
                                ))}
                              </div>
                            </div>
                            <div className="space-y-2">
                              <h4 className="text-sm font-medium text-text-muted">Scaling</h4>
                              <p className="text-sm text-text">
                                {report.plan.scaling.min_replicas}–{report.plan.scaling.max_replicas} replicas
                              </p>
                              <p className="text-xs text-text-muted">
                                Target CPU: {report.plan.scaling.target_cpu}%
                              </p>
                            </div>
                            <div className="space-y-2">
                              <h4 className="text-sm font-medium text-text-muted">Volumes</h4>
                              <div className="space-y-1">
                                {report.plan.volumes.map((vol) => (
                                  <p key={vol.name} className="text-sm text-text">
                                    {vol.name} → {vol.mount_path}
                                  </p>
                                ))}
                              </div>
                            </div>
                            <div className="space-y-2">
                              <h4 className="text-sm font-medium text-text-muted">Rollback</h4>
                              <p className="text-sm text-text">
                                {report.plan.rollback.strategy}
                              </p>
                              <p className="text-xs text-text-muted">
                                Max history: {report.plan.rollback.max_history}
                              </p>
                            </div>
                            <div className="space-y-2">
                              <h4 className="text-sm font-medium text-text-muted">Monitoring</h4>
                              <p className="text-sm text-text">
                                Health: {report.plan.monitoring.health_check_path}
                              </p>
                              <p className="text-xs text-text-muted">
                                Logging: {report.plan.monitoring.logging_level}
                              </p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {/* Infrastructure Diagram */}
                    {report.diagram && (
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-base">Infrastructure Diagram</CardTitle>
                          <CardDescription>{report.diagram.description}</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="flex flex-col gap-6">
                            {/* Services */}
                            <div className="flex flex-wrap gap-3">
                              {report.diagram.services.map((service) => (
                                <Card
                                  key={service.name}
                                  className="bg-surface-active min-w-[140px]"
                                >
                                  <CardContent className="p-3 text-center">
                                    <div className="flex justify-center mb-2">
                                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10 text-accent">
                                        {componentIcons[service.type] || componentIcons.default}
                                      </div>
                                    </div>
                                    <p className="text-sm font-medium text-text">
                                      {service.name}
                                    </p>
                                    <p className="text-xs text-text-muted">{service.type}</p>
                                    {service.port && (
                                      <p className="text-xs text-text-muted">
                                        Port {service.port}
                                      </p>
                                    )}
                                  </CardContent>
                                </Card>
                              ))}
                            </div>

                            {/* Connections */}
                            {report.diagram.connections.length > 0 && (
                              <div className="space-y-2">
                                <h4 className="text-sm font-medium text-text-muted">
                                  Connections
                                </h4>
                                <div className="space-y-1">
                                  {report.diagram.connections.map((conn, idx) => (
                                    <div
                                      key={idx}
                                      className="flex items-center gap-2 text-sm"
                                    >
                                      <span className="font-mono text-text">{conn.from}</span>
                                      <ChevronRight className="h-3 w-3 text-text-muted" />
                                      <span className="font-mono text-text">{conn.to}</span>
                                      <Badge variant="outline" className="ml-1 text-xs">
                                        {conn.protocol}
                                      </Badge>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {/* Report Sections */}
                    {report.sections && report.sections.length > 0 && (
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-base">Report Sections</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-4">
                            {report.sections
                              .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
                              .map((section, idx) => (
                                <div key={idx} className="rounded-lg border border-border p-4">
                                  <h4 className="mb-2 text-sm font-medium text-text">
                                    {section.title}
                                  </h4>
                                  <p className="text-sm text-text-muted whitespace-pre-wrap">
                                    {section.content}
                                  </p>
                                </div>
                              ))}
                          </div>
                        </CardContent>
                      </Card>
                    )}
                  </>
                );
              })()
            ) : (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                  <BarChart3 className="mb-4 h-12 w-12 text-text-muted" />
                  <h3 className="mb-2 text-lg font-semibold text-text">
                    No Report Generated
                  </h3>
                  <p className="max-w-sm text-sm text-text-muted">
                    Run analysis to generate a comprehensive deployment report with
                    infrastructure diagrams and deployment plans.
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      )}

      {/* Empty State */}
      {!hasData && !isLoading && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-accent/10">
              <Rocket className="h-8 w-8 text-accent" />
            </div>
            <h3 className="mb-2 text-lg font-semibold text-text">
              Welcome to Deployment Center
            </h3>
            <p className="max-w-md text-sm text-text-muted">
              Enter a repository path above and click Analyze to detect your project's
              infrastructure and generate deployment configurations including Docker,
              CI/CD, and Kubernetes manifests.
            </p>
            <div className="mt-6 flex flex-wrap items-center justify-center gap-4 text-sm text-text-muted">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-success" />
                Docker Analysis
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-success" />
                CI/CD Generation
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-success" />
                K8s Manifests
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-success" />
                Security Scan
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export { DeploymentCenter };
