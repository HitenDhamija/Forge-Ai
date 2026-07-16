"use client";

import { useState, useEffect } from "react";
import {
  Plus,
  MessageSquare,
  Trash2,
  PanelLeftClose,
  PanelLeft,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useConversationStore } from "@/stores/conversation-store";
import { useAIStore } from "@/stores/ai-store";
import { aiService } from "@/services/ai.service";
import { Skeleton } from "@/components/ui/skeleton";

export function ConversationSidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const {
    conversations,
    activeConversationId,
    setActiveConversation,
    setConversations,
    removeConversation,
    isLoading,
    setLoading,
  } = useConversationStore();
  const { activeModel } = useAIStore();

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    setLoading(true);
    try {
      const response = await aiService.getConversations();
      setConversations(response.data);
    } catch {
      // Silently fail
    } finally {
      setLoading(false);
    }
  };

  const handleNewConversation = async () => {
    try {
      const response = await aiService.createConversation(activeModel || undefined);
      useConversationStore.getState().addConversation(response.data);
    } catch {
      // Silently fail
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    try {
      await aiService.deleteConversation(id);
      removeConversation(id);
    } catch {
      // Silently fail
    }
  };

  if (collapsed) {
    return (
      <div className="flex flex-col items-center w-[52px] border-r border-border bg-bg py-3 gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCollapsed(false)}
          className="h-8 w-8"
          title="Expand sidebar"
        >
          <PanelLeft className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleNewConversation}
          className="h-8 w-8"
          title="New conversation"
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col w-[280px] border-r border-border bg-bg">
      <div className="flex items-center justify-between px-3 py-3 border-b border-border">
        <h2 className="text-sm font-semibold text-text">Conversations</h2>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCollapsed(true)}
          className="h-7 w-7"
        >
          <PanelLeftClose className="h-4 w-4" />
        </Button>
      </div>

      <div className="p-2">
        <Button
          variant="outline"
          onClick={handleNewConversation}
          className="w-full justify-start gap-2 text-sm"
        >
          <Plus className="h-4 w-4" />
          New conversation
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-2">
        {isLoading ? (
          <div className="space-y-2 p-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full rounded-lg" />
            ))}
          </div>
        ) : conversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center px-4">
            <MessageSquare className="h-8 w-8 text-text-muted mb-2" />
            <p className="text-sm text-text-muted">No conversations yet</p>
            <p className="text-xs text-text-muted mt-1">
              Start a new conversation to begin
            </p>
          </div>
        ) : (
          <div className="space-y-0.5">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                role="button"
                tabIndex={0}
                onClick={() => setActiveConversation(conv.id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    setActiveConversation(conv.id);
                  }
                }}
                className={cn(
                  "w-full flex items-start gap-2 px-3 py-2.5 rounded-lg text-left transition-colors group cursor-pointer",
                  activeConversationId === conv.id
                    ? "bg-surface-active text-text"
                    : "text-text-secondary hover:bg-surface-hover"
                )}
              >
                <MessageSquare className="h-4 w-4 mt-0.5 flex-shrink-0 opacity-50" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate font-medium">{conv.title}</p>
                  <p className="text-xs text-text-muted mt-0.5">
                    {conv.message_count} messages
                    {conv.updated_at && (
                      <> &middot; {formatRelativeTime(conv.updated_at)}</>
                    )}
                  </p>
                </div>
                <button
                  onClick={(e) => handleDelete(e, conv.id)}
                  className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-surface-active flex-shrink-0"
                  title="Delete conversation"
                >
                  <Trash2 className="h-3.5 w-3.5 text-text-muted hover:text-danger" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}
