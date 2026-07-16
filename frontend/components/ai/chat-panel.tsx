"use client";

import { useEffect, useRef } from "react";
import { useConversationStore } from "@/stores/conversation-store";
import { useStreamingStore } from "@/stores/streaming-store";
import { ChatMessageComponent } from "@/components/ai/chat-message";
import { ChatInput } from "@/components/ai/chat-input";
import { StreamingText } from "@/components/ai/streaming-text";
import { EmptyState } from "@/components/ai/empty-state";
import { Button } from "@/components/ui/button";
import { Square } from "lucide-react";

const SUGGESTED_PROMPTS = [
  "Explain the difference between TCP and UDP",
  "Write a Python function to sort a list",
  "What are best practices for REST API design?",
  "Help me debug a React useEffect hook",
];

export function ChatPanel() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const { activeConversationId, messages } = useConversationStore();
  const { isStreaming, streamContent } = useStreamingStore();

  const activeMessages = activeConversationId
    ? messages[activeConversationId] || []
    : [];

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [activeMessages, streamContent]);

  const isEmpty = activeMessages.length === 0 && !isStreaming;

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        {isEmpty ? (
          <EmptyState
            suggestedPrompts={SUGGESTED_PROMPTS}
          />
        ) : (
          <div className="max-w-3xl mx-auto py-6 px-4 space-y-6">
            {activeMessages.map((msg) => (
              <ChatMessageComponent key={msg.id} message={msg} />
            ))}

            {isStreaming && (
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-accent/20 flex items-center justify-center">
                  <span className="text-sm font-medium text-accent">AI</span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="rounded-xl bg-surface border border-border p-4">
                    <StreamingText content={streamContent} />
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="border-t border-border p-4">
        {isStreaming && (
          <div className="max-w-3xl mx-auto mb-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                const { cancelStreaming } = useStreamingStore.getState();
                cancelStreaming();
              }}
              className="gap-2"
            >
              <Square className="h-3 w-3" />
              Stop generating
            </Button>
          </div>
        )}
        <ChatInput />
      </div>
    </div>
  );
}
