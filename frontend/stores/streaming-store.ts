import { create } from "zustand";

interface StreamingState {
  isStreaming: boolean;
  streamContent: string;
  streamConversationId: string | null;
  streamStartTime: number | null;
}

interface StreamingActions {
  startStreaming: (conversationId: string) => void;
  appendToken: (token: string) => void;
  finishStreaming: () => void;
  cancelStreaming: () => void;
  getStreamDuration: () => number;
}

type StreamingStore = StreamingState & StreamingActions;

const initialState: StreamingState = {
  isStreaming: false,
  streamContent: "",
  streamConversationId: null,
  streamStartTime: null,
};

export const useStreamingStore = create<StreamingStore>()((set, get) => ({
  ...initialState,

  startStreaming: (conversationId) =>
    set({
      isStreaming: true,
      streamContent: "",
      streamConversationId: conversationId,
      streamStartTime: Date.now(),
    }),

  appendToken: (token) =>
    set((state) => ({
      streamContent: state.streamContent + token,
    })),

  finishStreaming: () =>
    set({
      isStreaming: false,
      streamStartTime: null,
    }),

  cancelStreaming: () => set(initialState),

  getStreamDuration: () => {
    const { streamStartTime } = get();
    if (!streamStartTime) return 0;
    return Date.now() - streamStartTime;
  },
}));
