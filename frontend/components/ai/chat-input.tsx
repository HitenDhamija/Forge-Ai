"use client";

import { useState, useRef, useCallback, type KeyboardEvent } from "react";
import { Send, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useConversationStore } from "@/stores/conversation-store";
import { useStreamingStore } from "@/stores/streaming-store";
import { useAIStore } from "@/stores/ai-store";
import { aiService } from "@/services/ai.service";
import { AI_CONFIG } from "@/config/constants";
import type { ChatMessage } from "@/types/ai";

export function ChatInput() {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { activeConversationId, addMessage, addConversation } =
    useConversationStore();
  const { isGenerating, setGenerating } = useAIStore();
  const {
    isStreaming,
    startStreaming,
    appendToken,
    finishStreaming,
    cancelStreaming,
  } = useStreamingStore();
  const { activeModel } = useAIStore();

  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, []);

  const handleInputChange = (value: string) => {
    if (value.length <= AI_CONFIG.MAX_PROMPT_LENGTH) {
      setInput(value);
      adjustHeight();
    }
  };

  const handleStop = useCallback(() => {
    aiService.stopStream();
    const currentContent = useStreamingStore.getState().streamContent;
    if (currentContent) {
      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: currentContent,
        timestamp: new Date().toISOString(),
      };
      const convId = useStreamingStore.getState().streamConversationId;
      if (convId) {
        addMessage(convId, assistantMessage);
      }
    }
    finishStreaming();
    setGenerating(false);
  }, [addMessage, finishStreaming, setGenerating]);

  const handleSend = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
      timestamp: new Date().toISOString(),
    };

    let convId = activeConversationId;

    if (!convId) {
      try {
        const response = await aiService.createConversation(
          activeModel || undefined
        );
        const conversation = response.data;
        addConversation(conversation);
        convId = conversation.id;
      } catch {
        return;
      }
    }

    addMessage(convId!, userMessage);
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    setGenerating(true);
    startStreaming(convId!);

    try {
      const { stream } = aiService.startStream({
        message: trimmed,
        model: activeModel || undefined,
        conversation_id: convId!,
        stream: true,
      });

      for await (const chunk of stream) {
        if (chunk.content) {
          appendToken(chunk.content);
        }
        if (chunk.done) {
          const assistantMessage: ChatMessage = {
            id: crypto.randomUUID(),
            role: "assistant",
            content: useStreamingStore.getState().streamContent,
            timestamp: chunk.created_at || new Date().toISOString(),
          };
          addMessage(convId!, assistantMessage);
          finishStreaming();
          setGenerating(false);
          return;
        }
      }

      const finalContent = useStreamingStore.getState().streamContent;
      if (finalContent) {
        const assistantMessage: ChatMessage = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: finalContent,
          timestamp: new Date().toISOString(),
        };
        addMessage(convId!, assistantMessage);
      }
      finishStreaming();
      setGenerating(false);
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") {
        const currentContent = useStreamingStore.getState().streamContent;
        if (currentContent) {
          const assistantMessage: ChatMessage = {
            id: crypto.randomUUID(),
            role: "assistant",
            content: currentContent,
            timestamp: new Date().toISOString(),
          };
          addMessage(convId!, assistantMessage);
        }
      }
      finishStreaming();
      setGenerating(false);
    }
  }, [
    input,
    isStreaming,
    activeConversationId,
    activeModel,
    addMessage,
    addConversation,
    setGenerating,
    startStreaming,
    appendToken,
    finishStreaming,
  ]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isDisabled = isStreaming || isGenerating;
  const charCount = input.length;
  const isNearLimit = charCount > AI_CONFIG.MAX_PROMPT_LENGTH * 0.9;

  return (
    <div className="max-w-3xl mx-auto w-full">
      <div className="relative rounded-xl border border-border bg-surface focus-within:border-accent transition-colors">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => handleInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message..."
          rows={1}
          disabled={isDisabled}
          className="w-full resize-none bg-transparent px-4 py-3 pr-24 text-sm text-text placeholder:text-text-muted focus:outline-none disabled:opacity-50 min-h-[44px] max-h-[200px]"
        />
        <div className="absolute right-2 bottom-2 flex items-center gap-2">
          <span
            className={`text-xs tabular-nums ${
              isNearLimit ? "text-warning" : "text-text-muted"
            }`}
          >
            {charCount}/{AI_CONFIG.MAX_PROMPT_LENGTH}
          </span>
          {isStreaming ? (
            <Button
              size="icon"
              variant="destructive"
              onClick={handleStop}
              className="h-8 w-8"
            >
              <Square className="h-3.5 w-3.5" />
            </Button>
          ) : (
            <Button
              size="icon"
              onClick={handleSend}
              disabled={!input.trim() || isDisabled}
              className="h-8 w-8"
            >
              <Send className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
      </div>
      <p className="mt-2 text-center text-xs text-text-muted">
        Press{" "}
        <kbd className="px-1 py-0.5 rounded bg-surface-hover text-text-secondary text-[10px]">
          Enter
        </kbd>{" "}
        to send,{" "}
        <kbd className="px-1 py-0.5 rounded bg-surface-hover text-text-secondary text-[10px]">
          Shift+Enter
        </kbd>{" "}
        for new line
      </p>
    </div>
  );
}
