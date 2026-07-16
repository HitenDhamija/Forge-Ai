"use client";

import { useState } from "react";
import { User, Bot, Copy, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ChatMessage } from "@/types/ai";

interface ChatMessageProps {
  message: ChatMessage;
}

export function ChatMessageComponent({ message }: ChatMessageProps) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={cn(
        "flex gap-3 group",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      <div
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center",
          isUser
            ? "bg-primary text-primary-text"
            : "bg-accent/20 text-accent"
        )}
      >
        {isUser ? (
          <User className="h-4 w-4" />
        ) : (
          <Bot className="h-4 w-4" />
        )}
      </div>

      <div
        className={cn(
          "flex-1 min-w-0",
          isUser ? "flex flex-col items-end" : ""
        )}
      >
        <div
          className={cn(
            "rounded-xl px-4 py-3 text-sm leading-relaxed max-w-full",
            isUser
              ? "bg-primary text-primary-text"
              : "bg-surface border border-border text-text"
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          ) : (
            <div className="whitespace-pre-wrap break-words prose-invert prose-sm max-w-none">
              {renderAssistantContent(message.content)}
            </div>
          )}
        </div>

        <div
          className={cn(
            "flex items-center gap-2 mt-1.5 text-xs text-text-muted",
            isUser ? "flex-row-reverse" : ""
          )}
        >
          <span>
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
          {!isUser && (
            <button
              onClick={handleCopy}
              className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-surface-hover"
              title="Copy message"
            >
              {copied ? (
                <Check className="h-3 w-3 text-success" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function renderAssistantContent(content: string) {
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
