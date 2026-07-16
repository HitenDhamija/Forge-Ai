"use client";

import * as React from "react";
import Link from "next/link";
import {
  Plus,
  Search,
  FolderKanban,
  MoreHorizontal,
  Grid3X3,
  List,
  Trash2,
  Settings,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/layouts/page-header";
import { useProjectStore } from "@/stores/project-store";
import { useDebounce } from "@/hooks/use-debounce";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export default function ProjectsPage() {
  const [searchQuery, setSearchQuery] = React.useState("");
  const [viewMode, setViewMode] = React.useState<"grid" | "list">("grid");
  const debouncedSearch = useDebounce(searchQuery);
  const { projects, removeProject } = useProjectStore();

  const filteredProjects = React.useMemo(() => {
    return projects.filter(
      (project) =>
        project.name.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
        project.description?.toLowerCase().includes(debouncedSearch.toLowerCase())
    );
  }, [projects, debouncedSearch]);

  return (
    <div>
      <PageHeader
        title="Projects"
        description="Manage and organize your projects"
        actions={
          <Link href="/projects/new">
            <Button leftIcon={<Plus className="h-4 w-4" />}>New Project</Button>
          </Link>
        }
      />

      {/* Search and Filter Bar */}
      <div className="mb-6 flex items-center justify-between">
        <div className="relative w-full max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
          <Input
            placeholder="Search projects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant={viewMode === "grid" ? "secondary" : "ghost"}
            size="icon"
            onClick={() => setViewMode("grid")}
          >
            <Grid3X3 className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === "list" ? "secondary" : "ghost"}
            size="icon"
            onClick={() => setViewMode("list")}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Projects Grid/List */}
      {filteredProjects.length === 0 ? (
        <EmptyState
          icon={<FolderKanban className="h-12 w-12" />}
          title="No projects found"
          description={
            searchQuery
              ? "No projects match your search criteria."
              : "Get started by creating your first project."
          }
          action={
            !searchQuery && (
              <Link href="/projects/new">
                <Button leftIcon={<Plus className="h-4 w-4" />}>Create Project</Button>
              </Link>
            )
          }
        />
      ) : viewMode === "grid" ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredProjects.map((project) => (
            <Link key={project.id} href={`/projects/${project.id}`} className="block">
              <Card className="group cursor-pointer transition-colors hover:border-text-muted">
                <CardHeader className="flex flex-row items-start justify-between space-y-0">
                  <div className="space-y-1">
                    <CardTitle className="text-lg">{project.name}</CardTitle>
                    <CardDescription className="line-clamp-2">
                      {project.description || "No description"}
                    </CardDescription>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="opacity-0 group-hover:opacity-100" onClick={(e) => e.preventDefault()}>
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem>
                        <Settings className="mr-2 h-4 w-4" /> Settings
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        className="text-danger focus:text-danger"
                        onClick={async (e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          if (!confirm(`Delete "${project.name}"?`)) return;
                          try {
                            await fetch(`http://127.0.0.1:8000/api/v1/projects/${project.id}`, {
                              method: "DELETE",
                              signal: AbortSignal.timeout(10000),
                            });
                          } catch {}
                          removeProject(project.id);
                        }}
                      >
                        <Trash2 className="mr-2 h-4 w-4" /> Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <Badge variant={project.status === "active" ? "success" : "secondary"}>
                      {project.status}
                    </Badge>
                    <span className="text-xs text-text-muted">
                      Updated {new Date(project.updatedAt).toLocaleDateString()}
                    </span>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {filteredProjects.map((project) => (
            <Link key={project.id} href={`/projects/${project.id}`} className="block">
              <Card className="cursor-pointer transition-colors hover:border-text-muted">
                <div className="flex items-center justify-between p-4">
                  <div className="flex items-center space-x-4">
                    <FolderKanban className="h-8 w-8 text-text-muted" />
                    <div>
                      <p className="font-medium">{project.name}</p>
                      <p className="text-sm text-text-muted">
                        {project.description || "No description"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <Badge variant={project.status === "active" ? "success" : "secondary"}>
                      {project.status}
                    </Badge>
                    <span className="text-xs text-text-muted">
                      Updated {new Date(project.updatedAt).toLocaleDateString()}
                    </span>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" onClick={(e) => e.preventDefault()}>
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>
                          <Settings className="mr-2 h-4 w-4" /> Settings
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-danger focus:text-danger"
                          onClick={async (e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            if (!confirm(`Delete "${project.name}"?`)) return;
                            try {
                              await fetch(`http://127.0.0.1:8000/api/v1/projects/${project.id}`, {
                                method: "DELETE",
                                signal: AbortSignal.timeout(10000),
                              });
                            } catch {}
                            removeProject(project.id);
                          }}
                        >
                          <Trash2 className="mr-2 h-4 w-4" /> Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
