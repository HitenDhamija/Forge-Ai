"use client";

import * as React from "react";
import {
  Upload,
  GitBranch,
  FolderOpen,
  FileArchive,
  X,
} from "lucide-react";
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalFooter,
} from "@/components/ui/modal";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ImportMethod } from "@/types/repository";

interface ImportModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onImport: (data: {
    name: string;
    description?: string;
    method: ImportMethod;
    file?: File;
    url?: string;
    folderFiles?: FileList;
    localPath?: string;
  }) => void;
  isImporting?: boolean;
  error?: string | null;
  progress?: string | null;
}

const IMPORT_METHODS: {
  id: ImportMethod;
  label: string;
  description: string;
  icon: React.ReactNode;
}[] = [
  {
    id: "zip",
    label: "ZIP Upload",
    description: "Upload a ZIP archive of your codebase",
    icon: <FileArchive className="h-5 w-5" />,
  },
  {
    id: "git",
    label: "Git URL",
    description: "Import from a Git repository URL",
    icon: <GitBranch className="h-5 w-5" />,
  },
  {
    id: "folder",
    label: "Local Folder",
    description: "Point to a local directory path",
    icon: <FolderOpen className="h-5 w-5" />,
  },
];

function ImportModal({
  open,
  onOpenChange,
  onImport,
  isImporting = false,
  error,
  progress,
}: ImportModalProps) {
  const [name, setName] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [method, setMethod] = React.useState<ImportMethod>("zip");
  const [url, setUrl] = React.useState("");
  const [file, setFile] = React.useState<File | null>(null);
  const [folderFiles, setFolderFiles] = React.useState<FileList | null>(null);
  const [localPath, setLocalPath] = React.useState("");
  const [isDragOver, setIsDragOver] = React.useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const folderInputRef = React.useRef<HTMLInputElement>(null);

  const resetForm = () => {
    setName("");
    setDescription("");
    setMethod("zip");
    setUrl("");
    setFile(null);
    setFolderFiles(null);
    setLocalPath("");
    if (fileInputRef.current) fileInputRef.current.value = "";
    if (folderInputRef.current) folderInputRef.current.value = "";
  };

  const handleOpenChange = (open: boolean) => {
    if (open) resetForm();
    onOpenChange(open);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile?.name.endsWith(".zip")) {
      setFile(droppedFile);
      if (!name) setName(droppedFile.name.replace(".zip", ""));
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      if (!name) setName(selectedFile.name.replace(".zip", ""));
    }
  };

  const handleFolderSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setFolderFiles(files);
      const firstPath = files[0].webkitRelativePath;
      const folderName = firstPath ? firstPath.split("/")[0] : "local-project";
      if (!name) setName(folderName);
    }
  };

  const handleSubmit = () => {
    if (!name.trim()) return;
    if (method === "zip" && !file) return;
    if (method === "git" && !url.trim()) return;
    if (method === "folder" && !localPath.trim() && !folderFiles) return;

    onImport({
      name: name.trim(),
      description: description.trim() || undefined,
      method,
      file: file || undefined,
      url: url.trim() || undefined,
      folderFiles: folderFiles || undefined,
      localPath: localPath.trim() || undefined,
    });
  };

  const isValid =
    name.trim() &&
    ((method === "zip" && file) ||
      (method === "git" && url.trim()) ||
      (method === "folder" && (localPath.trim() || folderFiles)));

  return (
    <Modal open={open} onOpenChange={handleOpenChange}>
      <ModalContent className="max-w-md">
        <ModalHeader>
          <ModalTitle>Import Repository</ModalTitle>
          <ModalDescription>
            Add a codebase for analysis and intelligence gathering.
          </ModalDescription>
        </ModalHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-text">
              Import Method
            </label>
            <div className="grid grid-cols-3 gap-2">
              {IMPORT_METHODS.map((m) => (
                <button
                  key={m.id}
                  onClick={() => setMethod(m.id)}
                  className={cn(
                    "flex flex-col items-center space-y-1 rounded-md border p-3 text-sm transition-colors",
                    method === m.id
                      ? "border-accent bg-accent/10 text-accent"
                      : "border-border bg-surface text-text-muted hover:bg-surface-hover"
                  )}
                >
                  {m.icon}
                  <span>{m.label}</span>
                </button>
              ))}
            </div>
          </div>

          <Input
            label="Repository Name"
            placeholder="my-project"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />

          <Textarea
            label="Description (optional)"
            placeholder="Brief description of the repository"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />

          {method === "zip" && (
            <div className="space-y-2">
              <label className="text-sm font-medium text-text">
                Upload ZIP File
              </label>
              <div
                onDrop={handleDrop}
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragOver(true);
                }}
                onDragLeave={() => setIsDragOver(false)}
                onClick={() => fileInputRef.current?.click()}
                className={cn(
                  "flex cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed p-6 transition-colors",
                  isDragOver
                    ? "border-accent bg-accent/5"
                    : "border-border hover:border-text-muted",
                  file && "border-success bg-success/5"
                )}
              >
                {file ? (
                  <div className="flex items-center space-x-2">
                    <FileArchive className="h-5 w-5 text-success" />
                    <span className="text-sm text-text">{file.name}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setFile(null);
                      }}
                      className="rounded p-1 hover:bg-surface-hover"
                    >
                      <X className="h-3 w-3 text-text-muted" />
                    </button>
                  </div>
                ) : (
                  <>
                    <Upload className="mb-2 h-8 w-8 text-text-muted" />
                    <p className="text-sm text-text-muted">
                      Drop a ZIP file here or click to browse
                    </p>
                  </>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".zip"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>
            </div>
          )}

          {method === "git" && (
            <Input
              label="Repository URL"
              placeholder="https://github.com/user/repo.git"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
          )}

          {method === "folder" && (
            <div className="space-y-3">
              <div className="space-y-2">
                <label className="text-sm font-medium text-text">
                  Local Folder Path (fast — no upload)
                </label>
              <Input
                placeholder="C:\Users\you\projects\my-repo"
                value={localPath}
                onChange={(e) => {
                  setLocalPath(e.target.value);
                  if (e.target.value) {
                    const parts = e.target.value.replace(/[\\/]+$/, "").split(/[\\/]/);
                    const folderName = parts[parts.length - 1];
                    if (folderName) setName(folderName);
                  }
                }}
              />
              </div>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-border" />
                </div>
                <div className="relative flex justify-center text-xs">
                  <span className="bg-surface px-2 text-text-muted">or upload via browser</span>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-text">
                  Browser Upload
                </label>
                <div
                  onClick={() => folderInputRef.current?.click()}
                  className={cn(
                    "flex cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed p-4 transition-colors",
                    folderFiles
                      ? "border-success bg-success/5"
                      : "border-border hover:border-text-muted"
                  )}
                >
                  {folderFiles ? (
                    <div className="flex items-center space-x-2">
                      <FolderOpen className="h-5 w-5 text-success" />
                      <span className="text-sm text-text">
                        {folderFiles.length} files selected
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setFolderFiles(null);
                        }}
                        className="rounded p-1 hover:bg-surface-hover"
                      >
                        <X className="h-3 w-3 text-text-muted" />
                      </button>
                    </div>
                  ) : (
                    <>
                      <FolderOpen className="mb-1 h-6 w-6 text-text-muted" />
                      <p className="text-sm text-text-muted">
                        Click to browse and select a folder
                      </p>
                      <p className="mt-1 text-xs text-text-muted">
                        Works best with small projects (&lt;1000 files)
                      </p>
                    </>
                  )}
                  <input
                    ref={folderInputRef}
                    type="file"
                    // @ts-ignore - webkitdirectory is a non-standard attribute
                    webkitdirectory=""
                    directory=""
                    multiple
                    onChange={handleFolderSelect}
                    className="hidden"
                  />
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="rounded-md bg-danger/10 p-3 text-sm text-danger">
              {error}
            </div>
          )}

          {progress && !error && (
            <div className="rounded-md bg-accent/10 p-3 text-sm text-accent flex items-center gap-2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-accent border-t-transparent" />
              {progress}
            </div>
          )}
        </div>

        <ModalFooter>
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={isImporting}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!isValid || isImporting}
            isLoading={isImporting}
            leftIcon={<Upload className="h-4 w-4" />}
          >
            Import Repository
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}

export { ImportModal };
