'use client';

import { Card } from '@/components/ui/card';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { useChat } from '@/src/hooks/useChat';
import { Button } from '@/components/ui/button';
import { RefreshCw } from 'lucide-react';
import { useChatStore } from '@/src/store/chatStore';

export function ChatInterface() {
  const { messages, isLoading, error, sendMessage } = useChat();
  const clearChat = useChatStore((state) => state.clearChat);

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="border-b p-4 bg-white flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Rural AI Doctor 🏥</h1>
          <p className="text-sm text-gray-600">Your AI Medical Assistant</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={clearChat}
          disabled={messages.length === 0}
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          New Chat
        </Button>
      </div>

      {/* Messages */}
      <Card className="flex-1 flex flex-col m-4 overflow-hidden">
        <MessageList messages={messages} isLoading={isLoading} />
        
        {error && (
          <div className="px-4 py-2 bg-red-50 border-t border-red-200">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
        
        <MessageInput onSend={sendMessage} disabled={isLoading} />
      </Card>
    </div>
  );
}