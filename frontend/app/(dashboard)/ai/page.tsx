"use client";

import { ChatPanel } from "@/components/ai/chat-panel";
import { ConversationSidebar } from "@/components/ai/conversation-sidebar";
import { ModelSelector } from "@/components/ai/model-selector";
import { StatusIndicator } from "@/components/ai/status-indicator";

export default function AIPage() {
  return (
    <div className="flex h-[calc(100vh-4rem)] -m-6">
      <ConversationSidebar />

      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center justify-between border-b border-border px-4 py-2">
          <ModelSelector />
          <StatusIndicator />
        </div>

        <ChatPanel />
      </div>
    </div>
  );
}
