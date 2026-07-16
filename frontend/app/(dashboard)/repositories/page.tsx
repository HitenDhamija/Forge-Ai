"use client";

import * as React from "react";
import { Plus, GitBranch } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SearchBar } from "@/components/ui/search-bar";
import { PageHeader } from "@/components/layouts/page-header";
import { RepositoryList } from "@/components/repositories/repository-list";
import { ImportModal } from "@/components/repositories/import-modal";
import { useRepositoryStore } from "@/stores/repository-store";
import { useProjectStore } from "@/stores/project-store";
import { repositoryService } from "@/services/repository.service";
import { useDebounce } from "@/hooks/use-debounce";

export default function RepositoriesPage() {
  const [searchQuery, setSearchQuery] = React.useState("");
  const [importOpen, setImportOpen] = React.useState(false);
  const [importProgress, setImportProgress] = React.useState<string | null>(null);
  const debouncedSearch = useDebounce(searchQuery);

  const {
    repositories,
    isLoading,
    isImporting,
    error,
    setRepositories,
    setLoading,
    setImporting,
    setError,
    clearError,
    addRepository,
  } = useRepositoryStore();

  const { addProject } = useProjectStore();

  React.useEffect(() => {
    loadRepositories();
  }, []);

  const loadRepositories = async () => {
    setLoading(true);
    try {
      const response = await repositoryService.list();
      setRepositories(response.data || []);
    } catch {
      setError("Failed to load repositories");
    } finally {
      setLoading(false);
    }
  };

  const filteredRepositories = React.useMemo(() => {
    if (!debouncedSearch) return repositories;
    const q = debouncedSearch.toLowerCase();
    return repositories.filter(
      (repo) =>
        repo.name.toLowerCase().includes(q) ||
        repo.description?.toLowerCase().includes(q)
    );
  }, [repositories, debouncedSearch]);

  const handleImport = async (data: {
    name: string;
    description?: string;
    method: "zip" | "git" | "folder";
    file?: File;
    url?: string;
    folderFiles?: FileList;
    localPath?: string;
  }) => {
    setImporting(true);
    clearError();
    try {
      let repoData: any;
      if (data.method === "zip" && data.file) {
        const formData = new FormData();
        formData.append("file", data.file);
        formData.append("name", data.name);
        if (data.description) formData.append("description", data.description);
        const response = await repositoryService.upload(formData);
        repoData = response.data;
        addRepository(repoData);
      } else if (data.method === "folder" && data.localPath) {
        // Local path import — copies directly from disk, no upload
        const BACKEND = "http://127.0.0.1:8000";
        setImportProgress("Importing from local path...");
        const formData = new FormData();
        formData.append("name", data.name);
        if (data.description) formData.append("description", data.description);
        formData.append("local_path", data.localPath);
        const response = await fetch(`${BACKEND}/api/v1/repositories/import/local-folder`, {
          method: "POST",
          body: formData,
        });
        if (!response.ok) {
          const errText = await response.text().catch(() => "Unknown error");
          throw new Error(`Failed to import: ${response.status} ${errText}`);
        }
        const result = await response.json();
        if (result.status === "error") {
          throw new Error(result.message || "Failed to import repository");
        }
        repoData = result.data;
        addRepository(repoData);
      } else if (data.method === "folder" && data.folderFiles) {
        // Browser upload — batch upload via HTTP
        const BACKEND = "http://127.0.0.1:8000";
        const BATCH_SIZE = 50;
        const totalFiles = data.folderFiles.length;

        setImportProgress("Initializing import...");
        const initForm = new FormData();
        initForm.append("name", data.name);
        if (data.description) initForm.append("description", data.description);
        const initRes = await fetch(`${BACKEND}/api/v1/repositories/import/folder/init`, {
          method: "POST",
          body: initForm,
        });
        if (!initRes.ok) {
          const errText = await initRes.text().catch(() => "Unknown error");
          throw new Error(`Failed to initialize import: ${initRes.status} ${errText}`);
        }
        const initData = await initRes.json();
        if (initData.status === "error") {
          throw new Error(initData.message || "Failed to initialize import");
        }
        const repoId = initData.data?.repo_id;
        if (!repoId) {
          throw new Error("No repository ID returned from server");
        }

        const totalBatches = Math.ceil(totalFiles / BATCH_SIZE);
        for (let start = 0; start < totalFiles; start += BATCH_SIZE) {
          const batchIndex = Math.floor(start / BATCH_SIZE) + 1;
          setImportProgress(`Uploading files (batch ${batchIndex}/${totalBatches})...`);
          const batch = Array.from(data.folderFiles).slice(start, start + BATCH_SIZE);
          const formData = new FormData();
          const paths: string[] = [];
          batch.forEach((f) => {
            const relPath = f.webkitRelativePath || f.name;
            paths.push(relPath);
            formData.append("files", f, relPath);
          });
          formData.append("paths", JSON.stringify(paths));
          const batchRes = await fetch(`${BACKEND}/api/v1/repositories/import/folder/${repoId}/batch`, {
            method: "POST",
            body: formData,
          });
          if (!batchRes.ok) {
            const errText = await batchRes.text().catch(() => "Unknown error");
            throw new Error(`Failed to upload file batch ${batchIndex}: ${batchRes.status} ${errText}`);
          }
          const batchData = await batchRes.json();
          if (batchData.status === "error") {
            throw new Error(batchData.message || `Failed to upload file batch ${batchIndex}`);
          }
        }

        setImportProgress("Analyzing repository...");
        const finalizeRes = await fetch(`${BACKEND}/api/v1/repositories/import/folder/${repoId}/finalize`, {
          method: "POST",
        });
        if (!finalizeRes.ok) {
          const errText = await finalizeRes.text().catch(() => "Unknown error");
          throw new Error(`Failed to finalize import: ${finalizeRes.status} ${errText}`);
        }
        const finalizeData = await finalizeRes.json();
        if (finalizeData.status === "error") {
          throw new Error(finalizeData.message || "Failed to analyze repository");
        }
        repoData = finalizeData.data;
        addRepository(repoData);
      } else {
        const response = await repositoryService.import({
          name: data.name,
          description: data.description,
          import_method: data.method,
          source_url: data.url,
        });
        repoData = response.data;
        addRepository(repoData);
      }

      // Auto-create a project linked to this repository (on backend)
      const langsArray = Array.isArray(repoData?.languages) ? repoData.languages : [];
      const languagesObj: Record<string, number> = {};
      langsArray.forEach((l: any) => { languagesObj[l.name] = l.percentage; });

      const fwArray = Array.isArray(repoData?.frameworks)
        ? repoData.frameworks.map((f: any) => typeof f === "string" ? f : f.name || "")
        : [];

      const BACKEND = "http://127.0.0.1:8000";
      let backendProject: any = null;
      try {
        const projRes = await fetch(`${BACKEND}/api/v1/projects`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: data.name,
            description: data.description || `Auto-created from ${data.method} import`,
            languages: Object.keys(languagesObj).filter(k => languagesObj[k] > 0),
            frameworks: fwArray,
          }),
          signal: AbortSignal.timeout(10000),
        });
        if (projRes.ok) {
          const projData = await projRes.json();
          backendProject = projData?.data;
        }
      } catch {
        // Non-critical — don't block import
      }

      const newProject = {
        id: backendProject?.id || crypto.randomUUID(),
        name: data.name,
        description: data.description || `Auto-created from ${data.method} import`,
        status: "active" as const,
        createdAt: new Date().toISOString().split("T")[0],
        updatedAt: new Date().toISOString().split("T")[0],
        userId: "user-1",
        repositoryId: repoData?.id,
        languages: languagesObj,
        frameworks: fwArray,
        fileCount: repoData?.file_count || 0,
        totalLines: repoData?.total_lines || 0,
      };
      addProject(newProject);

      // Auto-create a DYNAMIC workflow based on detected languages/frameworks
      const langNames = Object.keys(languagesObj).filter(k => languagesObj[k] > 0);
      const langLower = langNames.map(l => l.toLowerCase());

      const workflowTasks: { title: string; description: string }[] = [];

      // Step 1: Always analyze structure
      workflowTasks.push(
        { title: 'Analyze codebase structure', description: `Scan ${repoData?.file_count || 0} files across ${langNames.length} languages` },
      );

      // Step 2: Always review code quality
      workflowTasks.push(
        { title: 'Review code quality', description: 'Check for bugs, anti-patterns, and security issues' },
      );

      // Step 3: Language-specific security checks
      if (langLower.includes('javascript') || langLower.includes('typescript') || langLower.includes('jsx') || langLower.includes('tsx')) {
        workflowTasks.push(
          { title: 'Check for XSS vulnerabilities', description: 'Scan for innerHTML, document.write, eval, and unsafe DOM manipulation' },
        );
      }
      if (langLower.includes('python')) {
        workflowTasks.push(
          { title: 'Check for security vulnerabilities (bandit)', description: 'Scan for hardcoded secrets, SQL injection, unsafe deserialization, and eval usage' },
        );
      }
      if (langLower.includes('java')) {
        workflowTasks.push(
          { title: 'Check for Java security issues', description: 'Scan for deserialization flaws, XXE, SSRF, and insecure randomness' },
        );
      }
      if (langLower.includes('go')) {
        workflowTasks.push(
          { title: 'Check for Go security issues', description: 'Scan for unsafe pointer usage, SSRF, and unvalidated input' },
        );
      }
      if (langLower.includes('rust')) {
        workflowTasks.push(
          { title: 'Check for Rust safety issues', description: 'Scan for unsafe blocks, unwrap() calls, and potential panics' },
        );
      }
      if (langLower.includes('html') || langLower.includes('htm')) {
        workflowTasks.push(
          { title: 'Check for accessibility (a11y)', description: 'Scan for missing alt tags, ARIA attributes, and semantic HTML' },
        );
      }

      // Step 4: Framework-specific checks
      const fwLower = fwArray.map((f: string) => f.toLowerCase());
      if (fwLower.some((f: string) => ['react', 'next.js', 'vue', 'angular', 'svelte'].includes(f))) {
        workflowTasks.push(
          { title: 'Audit frontend bundle', description: 'Check for large dependencies, unused imports, and optimization opportunities' },
        );
      }
      if (fwLower.some((f: string) => ['express', 'node.js', 'fastapi', 'django', 'flask', 'spring'].includes(f))) {
        workflowTasks.push(
          { title: 'Check for rate limiting and input validation', description: 'Scan for missing rate limits, unvalidated user input, and CORS misconfigurations' },
        );
      }

      // Step 5: Check dependencies
      workflowTasks.push(
        { title: 'Check dependencies', description: 'Verify package.json / requirements.txt for outdated or vulnerable packages' },
      );

      // Step 6: Linting for applicable languages
      if (langLower.includes('python')) {
        workflowTasks.push(
          { title: 'Lint with flake8/ruff rules', description: 'Check for PEP 8 violations, unused imports, and code complexity' },
        );
      }
      if (langLower.includes('javascript') || langLower.includes('typescript')) {
        workflowTasks.push(
          { title: 'Check for console.log and debug artifacts', description: 'Scan for console.log, debugger statements, and TODO/FIXME markers' },
        );
      }

      // Step 7: Type checking for applicable languages
      if (langLower.includes('python')) {
        workflowTasks.push(
          { title: 'Check type hints (mypy)', description: 'Verify type annotations and suggest missing type hints' },
        );
      }
      if (langLower.includes('typescript') || langLower.includes('tsx')) {
        workflowTasks.push(
          { title: 'Check TypeScript strictness', description: 'Scan for any types, missing return types, and strict mode compliance' },
        );
      }

      // Step 8: Docker/CI checks
      const hasDocker = fwLower.some((f: string) => ['react', 'next.js', 'express', 'node.js', 'django', 'flask'].includes(f));
      if (hasDocker || langLower.includes('javascript') || langLower.includes('python')) {
        workflowTasks.push(
          { title: 'Generate deployment config', description: 'Create Dockerfile and CI/CD pipeline configuration' },
        );
      }

      // Step 9: Always generate report
      workflowTasks.push(
        { title: 'Generate analysis report', description: 'Compile findings into an actionable report' },
      );

      try {
        await fetch(`${BACKEND}/api/v1/workflows`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title: `Pipeline: ${data.name}`,
            description: `Automated analysis and quality pipeline for ${data.name} (${langNames.join(', ')})`,
            tasks: workflowTasks,
            risk_level: 'low',
            project_id: backendProject?.id || null,
          }),
          signal: AbortSignal.timeout(10000),
        });
      } catch {
        // Non-critical — don't block import
      }

      setImportOpen(false);
      loadRepositories();
    } catch (err: any) {
      const message = err?.message || "Failed to import repository";
      setError(message);
    } finally {
      setImportProgress(null);
      setImporting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this repository?")) return;
    try {
      await repositoryService.delete(id);
      useRepositoryStore.getState().removeRepository(id);
    } catch {
      setError("Failed to delete repository");
    }
  };

  return (
    <div>
      <PageHeader
        title="Repositories"
        description="Import and analyze codebases for intelligence gathering"
        actions={
          <Button
            leftIcon={<Plus className="h-4 w-4" />}
            onClick={() => setImportOpen(true)}
          >
            Import Repository
          </Button>
        }
      />

      <div className="mb-6">
        <SearchBar
          placeholder="Search repositories..."
          value={searchQuery}
          onChange={setSearchQuery}
          className="max-w-sm"
          shortcut={false}
        />
      </div>

      <RepositoryList
        repositories={filteredRepositories}
        isLoading={isLoading}
        searchQuery={debouncedSearch}
        onDelete={handleDelete}
      />

      <ImportModal
        key={importOpen ? "open" : "closed"}
        open={importOpen}
        onOpenChange={setImportOpen}
        onImport={handleImport}
        isImporting={isImporting}
        error={error}
        progress={importProgress}
      />
    </div>
  );
}
