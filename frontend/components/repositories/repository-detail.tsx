"use client";

import * as React from "react";
import {
  Layers,
  FileCode,
  Route,
  Database,
  Package,
  Network,
} from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArchitectureSummary } from "./architecture-summary";
import { LanguageBreakdown } from "./language-breakdown";
import { TechnologyCards } from "./technology-cards";
import { FolderTree } from "./folder-tree";
import { RoutesTable } from "./routes-table";
import { DatabaseTable } from "./database-table";
import { DependencyViewer } from "./dependency-viewer";
import type { AnalysisResult } from "@/types/repository";

interface RepositoryDetailProps {
  analysis: AnalysisResult;
}

type TabValue = "overview" | "code" | "routes" | "database" | "dependencies" | "graph";

function RepositoryDetail({ analysis }: RepositoryDetailProps) {
  const [activeTab, setActiveTab] = React.useState<TabValue>("overview");

  return (
    <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabValue)}>
      <TabsList className="mb-6">
        <TabsTrigger value="overview" className="gap-1.5">
          <Layers className="h-3.5 w-3.5" />
          Overview
        </TabsTrigger>
        <TabsTrigger value="code" className="gap-1.5">
          <FileCode className="h-3.5 w-3.5" />
          Code
        </TabsTrigger>
        <TabsTrigger value="routes" className="gap-1.5">
          <Route className="h-3.5 w-3.5" />
          Routes
        </TabsTrigger>
        <TabsTrigger value="database" className="gap-1.5">
          <Database className="h-3.5 w-3.5" />
          Database
        </TabsTrigger>
        <TabsTrigger value="dependencies" className="gap-1.5">
          <Package className="h-3.5 w-3.5" />
          Dependencies
        </TabsTrigger>
        <TabsTrigger value="graph" className="gap-1.5">
          <Network className="h-3.5 w-3.5" />
          Graph
        </TabsTrigger>
      </TabsList>

      <TabsContent value="overview" className="space-y-6">
        <ArchitectureSummary architecture={analysis.architecture} />
        <LanguageBreakdown languages={analysis.languages} />
        <TechnologyCards
          frameworks={analysis.frameworks}
          configFiles={analysis.config_files}
        />
        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-text-muted">
                Total Files
              </CardTitle>
            </CardHeader>
            <CardContent>
              <span className="text-2xl font-bold text-text">
                {analysis.total_files.toLocaleString()}
              </span>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-text-muted">
                Total Lines
              </CardTitle>
            </CardHeader>
            <CardContent>
              <span className="text-2xl font-bold text-text">
                {analysis.total_lines.toLocaleString()}
              </span>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-text-muted">
                Analysis Time
              </CardTitle>
            </CardHeader>
            <CardContent>
              <span className="text-2xl font-bold text-text">
                {(analysis.analysis_time_ms / 1000).toFixed(1)}s
              </span>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <TabsContent value="code" className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Folder Structure</CardTitle>
          </CardHeader>
          <CardContent>
            <FolderTree folders={analysis.folder_structure} />
          </CardContent>
        </Card>

        {analysis.code_elements.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                Code Elements ({analysis.code_elements.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="max-h-96 space-y-1 overflow-y-auto">
                {analysis.code_elements.map((el, idx) => (
                  <div
                    key={`${el.file_path}-${el.name}-${idx}`}
                    className="flex items-center justify-between rounded-md border border-border px-3 py-1.5 text-sm transition-colors hover:bg-surface-hover"
                  >
                    <div className="flex items-center space-x-2">
                      <span className="font-mono font-medium text-text">
                        {el.name}
                      </span>
                      <span className="text-xs text-text-muted">{el.type}</span>
                    </div>
                    <span className="font-mono text-xs text-text-muted">
                      {el.file_path}:{el.line_start}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </TabsContent>

      <TabsContent value="routes">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Detected API Routes ({analysis.routes.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <RoutesTable routes={analysis.routes} />
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="database">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Database Models ({analysis.database_models.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <DatabaseTable models={analysis.database_models} />
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="dependencies">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Dependencies ({analysis.dependencies.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <DependencyViewer dependencies={analysis.dependencies} />
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="graph">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Dependency Graph</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Network className="mb-4 h-12 w-12 text-text-muted" />
              <h3 className="mb-2 text-lg font-semibold text-text">
                Graph Visualization
              </h3>
              <p className="max-w-sm text-sm text-text-muted">
                Interactive dependency graph visualization coming soon. This will
                show module relationships and import paths.
              </p>
            </div>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
}

export { RepositoryDetail };
