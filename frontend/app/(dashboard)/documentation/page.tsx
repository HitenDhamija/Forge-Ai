"use client";

import * as React from "react";
import { Search, BookOpen, ChevronRight, FileText, Loader2, ArrowLeft, Sparkles, FolderGit2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/layouts/page-header";
import { apiClient } from "@/services/api";
import { useDebounce } from "@/hooks/use-debounce";

import { Button } from "@/components/ui/button";

interface RepoItem {
  id: string;
  name: string;
  status: string;
  file_count: number;
  languages: { name: string; lines: number; percentage: number }[];
}

interface DocItem {
  id: string;
  title: string;
  filename: string;
  category: string;
  size: number;
}

interface DocContent {
  id: string;
  title: string;
  filename: string;
  content: string;
  size: number;
}

const categoryLabels: Record<string, string> = {
  "getting-started": "Getting Started",
  "api": "API Reference",
  "architecture": "Architecture",
  "deployment": "Deployment",
  "troubleshooting": "Troubleshooting",
  "contributing": "Contributing",
  "general": "General",
};

export default function DocumentationPage() {
  const [searchQuery, setSearchQuery] = React.useState("");
  const [docs, setDocs] = React.useState<DocItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [selectedDoc, setSelectedDoc] = React.useState<DocContent | null>(null);
  const [loadingDoc, setLoadingDoc] = React.useState(false);
  const [generating, setGenerating] = React.useState(false);
  const [generateStatus, setGenerateStatus] = React.useState("");
  const debouncedSearch = useDebounce(searchQuery);

  const [repos, setRepos] = React.useState<RepoItem[]>([]);
  const [selectedRepoId, setSelectedRepoId] = React.useState<string>("");
  const [loadingRepos, setLoadingRepos] = React.useState(true);

  const loadRepos = async () => {
    try {
      const res = await apiClient.get("/repositories");
      const data = res.data;
      const repoList = Array.isArray(data) ? data : data?.repositories || data?.data || [];
      setRepos(repoList.filter((r: RepoItem) => r.status === "ready"));
      if (repoList.length > 0 && !selectedRepoId) {
        setSelectedRepoId(repoList[0].id);
      }
    } catch (err) {
      console.error("Failed to load repos:", err);
    } finally {
      setLoadingRepos(false);
    }
  };

  const loadDocs = async (repoId?: string) => {
    const rid = repoId || selectedRepoId;
    if (!rid) {
      setDocs([]);
      setLoading(false);
      return;
    }
    try {
      const res = await apiClient.get(`/documentation?repo_id=${rid}`);
      const data = res.data;
      setDocs(Array.isArray(data) ? data : data?.files || data?.data || []);
    } catch (err) {
      console.error("Failed to load docs:", err);
      setDocs([]);
    } finally {
      setLoading(false);
    }
  };

  const loadDoc = async (docId: string) => {
    if (!selectedRepoId) return;
    setLoadingDoc(true);
    try {
      const res = await apiClient.get(`/documentation/${docId}?repo_id=${selectedRepoId}`);
      const data = res.data;
      setSelectedDoc(data?.content ? data : data?.data || null);
    } catch (err) {
      console.error("Failed to load doc:", err);
    } finally {
      setLoadingDoc(false);
    }
  };

  const generateDocs = async () => {
    if (!selectedRepoId) return;
    setGenerating(true);
    setGenerateStatus("Analyzing codebase and generating documentation...");
    try {
      const res = await apiClient.post("/documentation/generate", {
        repo_id: selectedRepoId,
      });
      const data = res.data;
      const docsGenerated = data?.documents || data?.data?.documents || [];
      if (docsGenerated.length > 0) {
        setGenerateStatus(`Generated ${docsGenerated.length} documents`);
      } else {
        setGenerateStatus("Documentation generated successfully");
      }
      await loadDocs();
    } catch (err) {
      setGenerateStatus("Failed to generate documentation");
    } finally {
      setGenerating(false);
    }
  };

  React.useEffect(() => {
    loadRepos();
  }, []);

  React.useEffect(() => {
    if (selectedRepoId) {
      setLoading(true);
      loadDocs(selectedRepoId);
    }
  }, [selectedRepoId]);

  const groupedDocs = React.useMemo(() => {
    const groups: Record<string, DocItem[]> = {};
    for (const doc of docs) {
      const cat = doc.category || "general";
      if (!groups[cat]) groups[cat] = [];
      groups[cat].push(doc);
    }
    return groups;
  }, [docs]);

  const filteredGroups = React.useMemo(() => {
    if (!debouncedSearch) return groupedDocs;
    const q = debouncedSearch.toLowerCase();
    const filtered: Record<string, DocItem[]> = {};
    for (const [cat, items] of Object.entries(groupedDocs)) {
      const match = items.filter(
        (d) => d.title.toLowerCase().includes(q) || d.filename.toLowerCase().includes(q)
      );
      if (match.length > 0) filtered[cat] = match;
    }
    return filtered;
  }, [debouncedSearch, groupedDocs]);

  if (selectedDoc) {
    return (
      <div>
        <PageHeader
          title={selectedDoc.title}
          description={selectedDoc.filename}
          actions={
            <Button variant="outline" onClick={() => setSelectedDoc(null)}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Docs
            </Button>
          }
        />
        <Card>
          <CardContent className="p-6">
            <div className="prose prose-invert prose-sm max-w-none">
              {selectedDoc.content.split("\n").map((line, i) => {
                if (line.startsWith("# ")) return <h1 key={i} className="text-2xl font-bold mt-6 mb-3 text-text">{line.slice(2)}</h1>;
                if (line.startsWith("## ")) return <h2 key={i} className="text-xl font-semibold mt-5 mb-2 text-text">{line.slice(3)}</h2>;
                if (line.startsWith("### ")) return <h3 key={i} className="text-lg font-medium mt-4 mb-2 text-text">{line.slice(4)}</h3>;
                if (line.startsWith("- ")) return <li key={i} className="ml-4 text-text-secondary">{line.slice(2)}</li>;
                if (line.startsWith("```")) return null;
                if (line.trim() === "") return <br key={i} />;
                return <p key={i} className="text-text-secondary my-1">{line}</p>;
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Documentation"
        description={selectedRepoId ? `${docs.length} documents for ${repos.find(r => r.id === selectedRepoId)?.name || "repository"}` : "Select a repository to view documentation"}
      />

      {/* Repo Selector + Generate */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <FolderGit2 className="h-5 w-5 text-accent flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <label className="text-sm font-medium text-text block mb-1">Select Repository</label>
                {loadingRepos ? (
                  <div className="flex items-center gap-2 text-sm text-text-muted">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Loading repositories...
                  </div>
                ) : repos.length === 0 ? (
                  <p className="text-sm text-text-muted">No repositories imported yet. Import one first.</p>
                ) : (
                  <select
                    value={selectedRepoId}
                    onChange={(e) => setSelectedRepoId(e.target.value)}
                    className="w-full h-10 rounded-md border border-border bg-surface px-3 py-2 text-sm text-text focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                  >
                    {repos.map((repo) => (
                      <option key={repo.id} value={repo.id}>
                        {repo.name} ({repo.file_count} files{repo.languages?.[0] ? `, ${repo.languages[0].name}` : ""})
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </div>
            <Button onClick={generateDocs} disabled={generating || !selectedRepoId} className="flex-shrink-0">
              {generating ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="mr-2 h-4 w-4" />
              )}
              {generating ? "Generating..." : "Generate Documentation"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Generate Status */}
      {generateStatus && (
        <Card className="mb-6 border-accent/30 bg-accent/5">
          <CardContent className="pt-4 pb-4">
            <p className="text-sm text-text-secondary">{generateStatus}</p>
          </CardContent>
        </Card>
      )}

      {/* Search */}
      <div className="mb-8">
        <div className="relative max-w-xl">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
          <Input
            placeholder="Search documentation..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-accent" />
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          {Object.entries(filteredGroups).map(([category, items]) => (
            <Card key={category}>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BookOpen className="mr-2 h-5 w-5 text-accent" />
                  {categoryLabels[category] || category}
                </CardTitle>
                <CardDescription>{items.length} documents</CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1">
                  {items.map((doc) => (
                    <li key={doc.id}>
                      <button
                        onClick={() => loadDoc(doc.id)}
                        className="flex w-full items-center justify-between rounded-md p-2 text-sm text-text-muted transition-colors hover:bg-surface-hover hover:text-text"
                      >
                        <span className="flex items-center gap-2">
                          <FileText className="h-4 w-4" />
                          {doc.title}
                        </span>
                        <ChevronRight className="h-4 w-4" />
                      </button>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {Object.keys(filteredGroups).length === 0 && !loading && (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-text-muted mb-4">
              {selectedRepoId ? "No documentation generated yet for this repository." : "Select a repository to view documentation."}
            </p>
            <Button onClick={generateDocs} disabled={generating || !selectedRepoId}>
              <Sparkles className="mr-2 h-4 w-4" />
              Generate Documentation
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
