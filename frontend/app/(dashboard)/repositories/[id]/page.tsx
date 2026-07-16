"use client";

import * as React from "react";
import Link from "next/link";
import {
  ArrowLeft,
  GitBranch,
  FileCode,
  Layers,
  Clock,
  Play,
  AlertTriangle,
  AlertCircle,
  Info,
  Shield,
  Bug,
  Code,
  Package,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/layouts/page-header";
import { repositoryService } from "@/services/repository.service";

const SEV: Record<string, { color: string; icon: React.ReactNode; label: string; order: number }> = {
  CRITICAL: { color: "text-red-500", icon: <AlertCircle className="h-4 w-4" />, label: "Critical", order: 0 },
  HIGH: { color: "text-danger", icon: <AlertCircle className="h-4 w-4" />, label: "High", order: 1 },
  MEDIUM: { color: "text-warning", icon: <AlertTriangle className="h-4 w-4" />, label: "Medium", order: 2 },
  LOW: { color: "text-text-muted", icon: <Info className="h-4 w-4" />, label: "Low", order: 3 },
};

const CAT_ICONS: Record<string, React.ReactNode> = {
  security: <Shield className="h-4 w-4 text-danger" />,
  quality: <Code className="h-4 w-4 text-accent" />,
  best_practice: <CheckCircle2 className="h-4 w-4 text-success" />,
  dependency: <Package className="h-4 w-4 text-warning" />,
};

const CAT_LABELS: Record<string, string> = {
  security: "Security",
  quality: "Code Quality",
  best_practice: "Best Practice",
  dependency: "Dependency",
};

export default function RepositoryDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = React.use(params);
  const [repo, setRepo] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);
  const [analyzing, setAnalyzing] = React.useState(false);
  const [findings, setFindings] = React.useState<any[]>([]);
  const [showFindings, setShowFindings] = React.useState(false);
  const [filterCat, setFilterCat] = React.useState<string>("all");
  const [filterSev, setFilterSev] = React.useState<string>("all");

  React.useEffect(() => {
    async function load() {
      try {
        const response = await repositoryService.get(resolvedParams.id);
        setRepo(response.data);
      } catch {
        setRepo(null);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [resolvedParams.id]);

  async function handleAnalyze() {
    setAnalyzing(true);
    try {
      const result = await repositoryService.analyze(resolvedParams.id);
      if (result.data) {
        setRepo(result.data);
        setFindings(result.data.findings || []);
        setShowFindings(true);
        setFilterCat("all");
        setFilterSev("all");
      }
    } catch (err: any) {
      console.error("Analysis failed:", err);
    } finally {
      setAnalyzing(false);
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent" />
        <p className="mt-4 text-text-muted">Loading repository...</p>
      </div>
    );
  }

  if (!repo) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <GitBranch className="mb-4 h-12 w-12 text-text-muted" />
        <h2 className="text-xl font-semibold">Repository not found</h2>
        <p className="mt-2 text-text-muted">This repository may have been deleted or the server restarted.</p>
        <Link href="/repositories" className="mt-4">
          <Button variant="outline">Back to Repositories</Button>
        </Link>
      </div>
    );
  }

  const languages = Array.isArray(repo.languages) ? repo.languages : [];
  const frameworks = Array.isArray(repo.frameworks) ? repo.frameworks : [];

  const filtered = findings.filter((f) => {
    if (filterCat !== "all" && f.category !== filterCat) return false;
    if (filterSev !== "all" && f.severity !== filterSev) return false;
    return true;
  });

  const catCounts = { security: 0, quality: 0, best_practice: 0, dependency: 0 };
  const sevCounts = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
  findings.forEach((f) => {
    if (catCounts[f.category as keyof typeof catCounts] !== undefined) catCounts[f.category as keyof typeof catCounts]++;
    if (sevCounts[f.severity as keyof typeof sevCounts] !== undefined) sevCounts[f.severity as keyof typeof sevCounts]++;
  });

  return (
    <div>
      <Link href="/repositories" className="mb-4 inline-flex items-center text-sm text-text-muted hover:text-text">
        <ArrowLeft className="mr-1 h-4 w-4" /> Back to Repositories
      </Link>

      <PageHeader
        title={repo.name}
        description={repo.description || "No description"}
        actions={
          <div className="flex space-x-2">
            <Button
              variant="default"
              size="sm"
              leftIcon={<Play className="h-4 w-4" />}
              onClick={handleAnalyze}
              disabled={analyzing}
            >
              {analyzing ? "Analyzing..." : "Run Analysis"}
            </Button>
            <Badge variant={repo.status === "ready" ? "success" : "warning"}>
              {repo.status}
            </Badge>
          </div>
        }
      />

      {/* Stats */}
      <div className="mb-6 grid gap-4 sm:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-3">
              <FileCode className="h-8 w-8 text-accent" />
              <div>
                <p className="text-2xl font-bold">{repo.file_count || 0}</p>
                <p className="text-xs text-text-muted">Files</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-3">
              <Layers className="h-8 w-8 text-success" />
              <div>
                <p className="text-2xl font-bold">{(repo.total_lines || 0).toLocaleString()}</p>
                <p className="text-xs text-text-muted">Lines of Code</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-3">
              <Bug className="h-8 w-8 text-danger" />
              <div>
                <p className="text-2xl font-bold">{findings.length}</p>
                <p className="text-xs text-text-muted">Issues Found</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-3">
              <Clock className="h-8 w-8 text-warning" />
              <div>
                <p className="text-sm font-bold">
                  {repo.analyzed_at ? new Date(repo.analyzed_at).toLocaleDateString() : "N/A"}
                </p>
                <p className="text-xs text-text-muted">Last Analysis</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Findings */}
      {showFindings && findings.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Analysis Results ({findings.length} issues)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/* Category filters */}
            <div className="mb-3 flex flex-wrap gap-2">
              <button
                onClick={() => setFilterCat("all")}
                className={`rounded-full px-3 py-1 text-xs font-medium transition ${filterCat === "all" ? "bg-accent text-white" : "bg-surface text-text-muted hover:bg-surface-hover"}`}
              >
                All ({findings.length})
              </button>
              {(["security", "quality", "best_practice", "dependency"] as const).map((cat) => (
                <button
                  key={cat}
                  onClick={() => setFilterCat(cat)}
                  className={`flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium transition ${filterCat === cat ? "bg-accent text-white" : "bg-surface text-text-muted hover:bg-surface-hover"}`}
                >
                  {CAT_ICONS[cat]} {CAT_LABELS[cat]} ({catCounts[cat]})
                </button>
              ))}
            </div>

            {/* Severity filters */}
            <div className="mb-4 flex flex-wrap gap-2">
              {(["CRITICAL", "HIGH", "MEDIUM", "LOW"] as const).map((sev) => (
                <button
                  key={sev}
                  onClick={() => setFilterSev(filterSev === sev ? "all" : sev)}
                  className={`rounded-full px-3 py-1 text-xs font-medium transition ${filterSev === sev ? "bg-accent text-white" : "bg-surface text-text-muted hover:bg-surface-hover"}`}
                >
                  {SEV[sev].label} ({sevCounts[sev]})
                </button>
              ))}
            </div>

            {/* Findings list */}
            <div className="max-h-96 space-y-2 overflow-y-auto">
              {filtered.length === 0 && (
                <p className="py-4 text-center text-sm text-text-muted">No issues match the current filters.</p>
              )}
              {filtered.map((f, i) => {
                const sev = SEV[f.severity] || SEV.LOW;
                return (
                  <div key={i} className="flex items-start gap-3 rounded-md border border-border p-3 text-sm hover:bg-surface-hover/50">
                    <span className={`mt-0.5 flex-shrink-0 ${sev.color}`}>{sev.icon}</span>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant={f.severity === "CRITICAL" || f.severity === "HIGH" ? "destructive" : f.severity === "MEDIUM" ? "warning" : "secondary"}>
                          {sev.label}
                        </Badge>
                        <Badge variant="outline" className="flex items-center gap-1">
                          {CAT_ICONS[f.category]} {CAT_LABELS[f.category]}
                        </Badge>
                        <span className="text-xs text-text-muted">{f.file}{f.line ? `:${f.line}` : ""}</span>
                      </div>
                      <p className="mt-1">{f.message}</p>
                      {f.snippet && (
                        <pre className="mt-2 overflow-x-auto rounded bg-surface px-3 py-2 text-xs text-text-muted">
                          {f.snippet}
                        </pre>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Languages */}
      {languages.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Languages</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {languages.map((lang: any) => (
                <div key={lang.name}>
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span className="font-medium">{lang.name}</span>
                    <span className="text-text-muted">{lang.percentage}% ({lang.lines} lines)</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-surface">
                    <div
                      className="h-full rounded-full bg-accent transition-all"
                      style={{ width: `${lang.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Frameworks */}
      {frameworks.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Frameworks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {frameworks.map((fw: any) => (
                <Badge key={typeof fw === "string" ? fw : fw.name} variant="secondary">
                  {typeof fw === "string" ? fw : fw.name}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
