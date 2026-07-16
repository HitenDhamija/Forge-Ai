"use client";

import * as React from "react";
import Link from "next/link";
import {
  ArrowLeft,
  GitBranch,
  Bot,
  Workflow,
  BarChart3,
  Trash2,
  FolderKanban,
  FileCode,
  Layers,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/layouts/page-header";
import { useProjectStore } from "@/stores/project-store";
import { useRouter } from "next/navigation";

export default function ProjectDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const { projects, removeProject } = useProjectStore();
  const resolvedParams = React.use(params);
  const [hydrated, setHydrated] = React.useState(false);

  React.useEffect(() => {
    setHydrated(true);
  }, []);

  const project = projects.find((p) => p.id === resolvedParams.id);

  React.useEffect(() => {
    if (hydrated && !project) {
      router.replace("/projects");
    }
  }, [hydrated, project, router]);

  if (!hydrated || !project) return null;

  const handleDelete = async () => {
    if (!confirm(`Delete "${project.name}"?`)) return;
    const id = project.id;
    try {
      await fetch(`http://127.0.0.1:8000/api/v1/projects/${id}`, {
        method: "DELETE",
        signal: AbortSignal.timeout(10000),
      });
    } catch {}
    removeProject(id);
    router.push("/projects");
  };

  const hasRepo = !!project.repositoryId;

  // Normalize languages — handle both {name: pct} and numeric-keyed {0: {name, lines, pct}}
  const rawLangs = project.languages || {};
  const languages: Record<string, number> = {};
  for (const [key, val] of Object.entries(rawLangs)) {
    if (typeof val === "number") {
      languages[key] = val;
    } else if (typeof val === "object" && val !== null) {
      const obj = val as any;
      const name = obj.name || obj.language || key;
      languages[name] = obj.percentage || obj.lines || 0;
    }
  }
  const topLanguages = Object.entries(languages)
    .filter(([, v]) => v > 0)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  return (
    <div>
      <Link href="/projects" className="mb-4 inline-flex items-center text-sm text-text-muted hover:text-text">
        <ArrowLeft className="mr-1 h-4 w-4" /> Back to Projects
      </Link>

      <PageHeader
        title={project.name}
        description={project.description || "No description"}
        actions={
          <div className="flex space-x-2">
            <Badge variant={project.status === "active" ? "success" : "secondary"}>
              {project.status}
            </Badge>
            <Button variant="ghost" size="icon" onClick={handleDelete}>
              <Trash2 className="h-4 w-4 text-danger" />
            </Button>
          </div>
        }
      />

      {/* Repository Analysis */}
      {hasRepo && (
        <div className="mb-6 grid gap-4 sm:grid-cols-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-3">
                <FileCode className="h-8 w-8 text-accent" />
                <div>
                  <p className="text-2xl font-bold">{project.fileCount || 0}</p>
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
                  <p className="text-2xl font-bold">{(project.totalLines || 0).toLocaleString()}</p>
                  <p className="text-xs text-text-muted">Lines of Code</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-3">
                <GitBranch className="h-8 w-8 text-warning" />
                <div>
                  <p className="text-2xl font-bold">{topLanguages.length}</p>
                  <p className="text-xs text-text-muted">Languages</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-3">
                <Layers className="h-8 w-8 text-danger" />
                <div>
                  <p className="text-2xl font-bold">{project.frameworks?.length || 0}</p>
                  <p className="text-xs text-text-muted">Frameworks</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Languages */}
      {hasRepo && topLanguages.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Languages</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {topLanguages.map(([lang, pct]) => {
                const percent = Math.min(Math.round(pct), 100);
                return (
                  <div key={lang}>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="font-medium">{lang}</span>
                      <span className="text-text-muted">{percent}%</span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-surface">
                      <div
                        className="h-full rounded-full bg-accent transition-all"
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Frameworks */}
      {hasRepo && project.frameworks && project.frameworks.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Frameworks Detected</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {project.frameworks.map((fw) => (
                <Badge key={fw} variant="secondary">{fw}</Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2">
            {[
              { icon: GitBranch, title: "View Repository", href: project.repositoryId ? `/repositories/${project.repositoryId}` : "/repositories", color: "text-accent" },
              { icon: Bot, title: "AI Agents", href: "/agents", color: "text-success" },
              { icon: Workflow, title: "Workflows", href: `/workflows?project_id=${project.id}`, color: "text-warning" },
              { icon: BarChart3, title: "Monitoring", href: "/monitoring", color: "text-danger" },
            ].map((f) => (
              <Link key={f.title} href={f.href}>
                <div className="flex items-start space-x-3 rounded-md border border-border p-4 transition-colors hover:border-text-muted hover:bg-surface-hover">
                  <f.icon className={`mt-0.5 h-5 w-5 ${f.color}`} />
                  <div>
                    <p className="font-medium">{f.title}</p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
