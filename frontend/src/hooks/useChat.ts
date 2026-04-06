import { useState } from 'react';
import { useChatStore } from '../store/chatStore';
import { chatAPI } from '../lib/api/chat';
import { Message } from '../types/chat';

async function getCurrentLocation(): Promise<{ lat: number; lng: number } | undefined> {
  if (typeof window === 'undefined' || !navigator.geolocation) {
    return undefined;
  }

  return new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        });
      },
      () => resolve(undefined),
      // Slightly longer timeout and non-high-accuracy mode improve success rate on desktop browsers.
      { enableHighAccuracy: false, timeout: 12000, maximumAge: 120000 },
    );
  });
}

export function useChat() {
  const { messages, sessionId, isLoading, addMessage, setSessionId, setLoading } = useChatStore();
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async (content: string) => {
    try {
      setError(null);
      setLoading(true);

      
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content,
        timestamp: new Date(),
      };
      addMessage(userMessage);

      
      const userLocation = await getCurrentLocation();
      const request = {
        messages: [
          ...messages.map(m => ({ role: m.role, content: m.content })),
          { role: 'user' as const, content },
        ],
        session_id: sessionId || undefined,
        user_location: userLocation,
      };

      
      const response = await chatAPI.sendMessage(request);

      
      if (!sessionId) {
        setSessionId(response.session_id);
      }

      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date(response.timestamp),
        metadata: response.metadata,
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
