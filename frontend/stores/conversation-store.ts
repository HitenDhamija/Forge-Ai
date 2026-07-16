import { create } from "zustand";
import type { Conversation, ChatMessage } from "@/types/ai";

interface ConversationState {
  conversations: Conversation[];
  activeConversationId: string | null;
  messages: Record<string, ChatMessage[]>;
  isLoading: boolean;
}

interface ConversationActions {
  setConversations: (conversations: Conversation[]) => void;
  setActiveConversation: (id: string | null) => void;
  addConversation: (conversation: Conversation) => void;
  removeConversation: (id: string) => void;
  addMessage: (conversationId: string, message: ChatMessage) => void;
  setMessages: (conversationId: string, messages: ChatMessage[]) => void;
  clearMessages: (conversationId: string) => void;
  getActiveMessages: () => ChatMessage[];
  setLoading: (loading: boolean) => void;
}

type ConversationStore = ConversationState & ConversationActions;

export const useConversationStore = create<ConversationStore>()((set, get) => ({
  conversations: [],
  activeConversationId: null,
  messages: {},
  isLoading: false,

  setConversations: (conversations) => set({ conversations }),

  setActiveConversation: (id) => set({ activeConversationId: id }),

  addConversation: (conversation) =>
    set((state) => ({
      conversations: [conversation, ...state.conversations],
      activeConversationId: conversation.id,
      messages: {
        ...state.messages,
        [conversation.id]: conversation.messages || [],
      },
    })),

  removeConversation: (id) =>
    set((state) => {
      const { [id]: _, ...remainingMessages } = state.messages;
      const newConversations = state.conversations.filter((c) => c.id !== id);
      const newActiveId =
        state.activeConversationId === id
          ? newConversations[0]?.id || null
          : state.activeConversationId;
      return {
        conversations: newConversations,
        activeConversationId: newActiveId,
        messages: remainingMessages,
      };
    }),

  addMessage: (conversationId, message) =>
    set((state) => ({
      messages: {
        ...state.messages,
        [conversationId]: [...(state.messages[conversationId] || []), message],
      },
      conversations: state.conversations.map((c) =>
        c.id === conversationId
          ? { ...c, message_count: c.message_count + 1, updated_at: new Date().toISOString() }
          : c
      ),
    })),

  setMessages: (conversationId, msgs) =>
    set((state) => ({
      messages: {
        ...state.messages,
        [conversationId]: msgs,
      },
    })),

  clearMessages: (conversationId) =>
    set((state) => ({
      messages: {
        ...state.messages,
        [conversationId]: [],
      },
    })),

  getActiveMessages: () => {
    const { activeConversationId, messages } = get();
    if (!activeConversationId) return [];
    return messages[activeConversationId] || [];
  },

  setLoading: (loading) => set({ isLoading: loading }),
}));
