"use client";

import { useState, useEffect, useRef } from "react";
import { ChevronDown, Check, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useAIStore } from "@/stores/ai-store";
import { aiService } from "@/services/ai.service";
import { AI_CONFIG } from "@/config/constants";
import type { ModelInfo } from "@/types/ai";

export function ModelSelector() {
  const [open, setOpen] = useState(false);
  const [switching, setSwitching] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { activeModel, availableModels, setActiveModel, setAvailableModels, ollamaConnected } =
    useAIStore();

  useEffect(() => {
    loadModels();
  }, []);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const loadModels = async () => {
    try {
      const response = await aiService.getModels();
      setAvailableModels(response.data.models);
      if (!activeModel && response.data.active_model) {
        setActiveModel(response.data.active_model);
      }
    } catch {
      // Silently fail
    }
  };

  const handleSwitch = async (modelName: string) => {
    if (modelName === activeModel || switching) return;
    setSwitching(true);
    try {
      await aiService.switchModel(modelName);
      setActiveModel(modelName);
      setOpen(false);
    } catch {
      // Silently fail
    } finally {
      setSwitching(false);
    }
  };

  const formatSize = (size: number | null) => {
    if (!size) return "";
    const gb = size / (1024 * 1024 * 1024);
    if (gb >= 1) return `${gb.toFixed(1)} GB`;
    const mb = size / (1024 * 1024);
    return `${mb.toFixed(0)} MB`;
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <Button
        variant="ghost"
        onClick={() => setOpen(!open)}
        disabled={!ollamaConnected}
        className="gap-2 text-sm font-medium"
      >
        {switching ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <span className="font-mono text-xs">{activeModel || AI_CONFIG.DEFAULT_MODEL}</span>
        )}
        <ChevronDown className={cn("h-4 w-4 transition-transform", open && "rotate-180")} />
      </Button>

      {open && (
        <div className="absolute top-full left-0 mt-1 w-72 rounded-xl border border-border bg-surface shadow-xl z-50 py-1">
          <div className="px-3 py-2 border-b border-border">
            <p className="text-xs font-medium text-text-muted">Select Model</p>
          </div>
          <div className="max-h-64 overflow-y-auto py-1">
            {availableModels.length === 0 ? (
              <div className="px-3 py-4 text-center text-sm text-text-muted">
                {ollamaConnected ? "No models available" : "Ollama not connected"}
              </div>
            ) : (
              availableModels.map((model) => (
                <button
                  key={model.name}
                  onClick={() => handleSwitch(model.name)}
                  className={cn(
                    "w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-surface-hover transition-colors",
                    activeModel === model.name && "bg-surface-active"
                  )}
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-text truncate">{model.name}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      {model.parameter_size && (
                        <span className="text-xs text-text-muted">{model.parameter_size}</span>
                      )}
                      {model.size && (
                        <span className="text-xs text-text-muted">{formatSize(model.size)}</span>
                      )}
                      {model.quantization && (
                        <span className="text-xs text-text-muted">{model.quantization}</span>
                      )}
                    </div>
                  </div>
                  {activeModel === model.name && (
                    <Check className="h-4 w-4 text-accent flex-shrink-0" />
                  )}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
