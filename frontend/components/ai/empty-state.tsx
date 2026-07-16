"use client";

import { Brain } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useConversationStore } from "@/stores/conversation-store";
import { useAIStore } from "@/stores/ai-store";
import { aiService } from "@/services/ai.service";

interface EmptyStateProps {
  suggestedPrompts?: string[];
}

export function EmptyState({ suggestedPrompts = [] }: EmptyStateProps) {
  const { addConversation } = useConversationStore();
  const { activeModel } = useAIStore();

  const handlePromptClick = async (prompt: string) => {
    try {
      const response = await aiService.createConversation(activeModel || undefined);
      const conversation = response.data;
      addConversation(conversation);

      const userMessage = {
        id: crypto.randomUUID(),
        role: "user" as const,
        content: prompt,
        timestamp: new Date().toISOString(),
      };
      useConversationStore.getState().addMessage(conversation.id, userMessage);
    } catch {
      // Silently fail
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-full px-4">
      <div className="w-16 h-16 rounded-2xl bg-accent/10 flex items-center justify-center mb-6">
        <Brain className="h-8 w-8 text-accent" />
      </div>

      <h2 className="text-xl font-semibold text-text mb-2">
        Start a conversation
      </h2>
      <p className="text-sm text-text-muted mb-8 max-w-md text-center">
        Ask questions, get help with code, brainstorm ideas, or explore topics with your AI assistant.
      </p>

      {suggestedPrompts.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full">
          {suggestedPrompts.map((prompt, i) => (
            <Button
              key={i}
              variant="outline"
              className="justify-start text-left h-auto py-3 px-4 text-sm text-text-secondary hover:text-text whitespace-normal"
              onClick={() => handlePromptClick(prompt)}
            >
              {prompt}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}
