import { useState } from 'react';
import { useChatStore } from '../store/chatStore';
import { chatAPI } from '../lib/api/chat';
import { Message } from '../types/chat';

export function useChat() {
  const { messages, sessionId, isLoading, addMessage, setSessionId, setLoading } = useChatStore();
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async (content: string) => {
    try {
      setError(null);
      setLoading(true);

      // Add user message immediately
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content,
        timestamp: new Date(),
      };
      addMessage(userMessage);

      // Prepare request
      const request = {
        messages: [
          ...messages.map(m => ({ role: m.role, content: m.content })),
          { role: 'user' as const, content },
        ],
        session_id: sessionId || undefined,
      };

      // Send to backend
      const response = await chatAPI.sendMessage(request);

      // Update session ID if new
      if (!sessionId) {
        setSessionId(response.session_id);
      }

      // Add assistant message
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date(response.timestamp),
      };
      addMessage(assistantMessage);

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send message');
      console.error('Chat error:', err);
    } finally {
      setLoading(false);
    }
  };

  return {
    messages,
    isLoading,
    error,
    sendMessage,
  };
}