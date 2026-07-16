"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { AI_CONFIG } from "@/config/constants";

interface StreamingTextProps {
  content: string;
  className?: string;
}

export function StreamingText({ content, className }: StreamingTextProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [content]);

  if (!content) {
    return (
      <div className={cn("flex items-center gap-1.5", className)}>
        <span className="h-1.5 w-1.5 rounded-full bg-accent animate-bounce [animation-delay:0ms]" />
        <span className="h-1.5 w-1.5 rounded-full bg-accent animate-bounce [animation-delay:150ms]" />
        <span className="h-1.5 w-1.5 rounded-full bg-accent animate-bounce [animation-delay:300ms]" />
      </div>
    );
  }

  return (
    <div ref={containerRef} className={cn("text-sm leading-relaxed", className)}>
      <div className="whitespace-pre-wrap break-words">
        {renderContent(content)}
      </div>
      <span className="inline-block w-2 h-4 ml-0.5 bg-accent animate-pulse align-text-bottom" />
    </div>
  );
}

function renderContent(content: string) {
  const parts = content.split(/(```[\s\S]*?```)/g);

  return parts.map((part, i) => {
    if (part.startsWith("```") && part.endsWith("```")) {
      const lines = part.slice(3, -3);
      const firstNewline = lines.indexOf("\n");
      const language = firstNewline > 0 ? lines.slice(0, firstNewline).trim() : "";
      const code = firstNewline > 0 ? lines.slice(firstNewline + 1) : lines;

      return (
        <div key={i} className="my-3 rounded-lg border border-border overflow-hidden">
          {language && (
            <div className="px-3 py-1.5 bg-bg-elevated border-b border-border text-xs text-text-muted">
              {language}
            </div>
          )}
          <pre className="p-3 bg-bg-elevated overflow-x-auto">
            <code className="text-xs font-mono text-text-secondary">{code}</code>
          </pre>
        </div>
      );
    }

    const inlineParts = part.split(/(`[^`]+`)/g);
    return (
      <span key={i}>
        {inlineParts.map((ip, j) => {
          if (ip.startsWith("`") && ip.endsWith("`")) {
            return (
              <code
                key={j}
                className="px-1.5 py-0.5 rounded bg-surface-hover text-accent text-xs font-mono"
              >
                {ip.slice(1, -1)}
              </code>
            );
          }
          return <span key={j}>{ip}</span>;
        })}
      </span>
    );
  });
}
