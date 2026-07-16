"use client";

import { useEffect } from "react";
import { Wifi, WifiOff } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAIStore } from "@/stores/ai-store";
import { aiService } from "@/services/ai.service";

export function StatusIndicator() {
  const { ollamaConnected, ollamaVersion, activeModel, modelsCount, setOllamaStatus } =
    useAIStore();

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkStatus = async () => {
    try {
      const response = await aiService.getStatus();
      setOllamaStatus(response.data);
    } catch {
      useAIStore.getState().setOllamaStatus({
        connected: false,
        version: null,
        models_count: 0,
        running_models: [],
      });
    }
  };

  return (
    <div className="flex items-center gap-3">
      <div
        className={cn(
          "flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-medium",
          ollamaConnected
            ? "bg-success/10 text-success"
            : "bg-danger/10 text-danger"
        )}
      >
        <span
          className={cn(
            "h-2 w-2 rounded-full",
            ollamaConnected ? "bg-success animate-pulse" : "bg-danger"
          )}
        />
        {ollamaConnected ? "Connected" : "Offline — run `ollama serve`"}
      </div>

      {ollamaConnected && (
        <div className="hidden sm:flex items-center gap-2 text-xs text-text-muted">
          {activeModel && (
            <span className="font-mono">{activeModel}</span>
          )}
          {modelsCount > 0 && (
            <>
              <span>&middot;</span>
              <span>{modelsCount} models</span>
            </>
          )}
          {ollamaVersion && (
            <>
              <span>&middot;</span>
              <span>v{ollamaVersion}</span>
            </>
          )}
        </div>
      )}
    </div>
  );
}
