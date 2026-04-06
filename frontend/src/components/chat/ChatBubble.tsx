import { Message } from '@/types/chat';
import { Button } from '@/components/ui/button';
import { cn } from 'lib/utils';
import { User, Bot, ExternalLink, PhoneCall, Copy } from 'lucide-react';

interface ChatBubbleProps {
  message: Message;
}

export function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.role === 'user';
  const isCriticalAssistant = !isUser && message.metadata?.status === 'CRITICAL';
  const metadata: any = message.metadata || {};
  const criticalMeta =
    metadata?.emergency_info && typeof metadata.emergency_info === 'object'
      ? { ...metadata.emergency_info, ...metadata, status: metadata.status ?? metadata.emergency_info.status }
      : metadata;
  const nearestFacility = criticalMeta?.nearby_facilities?.[0];
  const fallbackFromText = (() => {
    const match = message.content.match(/Nearest CHC:\s*(.+?)\s*\(([\d.]+)\s*km\)\s*\|\s*([+\d\- ]+)/i);
    if (!match) return null;
    return {
      name: match[1].trim(),
      contact_number: match[3].trim(),
    };
  })();
  const facilityName = nearestFacility?.name || fallbackFromText?.name;
  const rawPhone = nearestFacility?.contact_number || fallbackFromText?.contact_number || '';
  const phone = rawPhone.replace(/[^\d+]/g, '');
  const mapsUrl = 'https://www.google.com/maps/search/?api=1&query=hospital+near+me';
  const parsedTimestamp = message.timestamp instanceof Date
    ? message.timestamp
    : new Date(message.timestamp as unknown as string);
  const timeLabel = Number.isNaN(parsedTimestamp.getTime())
    ? 'Unknown time'
    : parsedTimestamp.toLocaleTimeString();

  return (
    <div className={cn(
      'flex gap-3 mb-4',
      isUser ? 'flex-row-reverse' : 'flex-row'
    )}>
      <div className={cn(
        'shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
        isUser ? 'bg-blue-500' : 'bg-green-500'
      )}>
        {isUser ? (
          <User className="w-5 h-5 text-white" />
        ) : (
          <Bot className="w-5 h-5 text-white" />
        )}
      </div>

      <div className={cn(
        'flex flex-col max-w-[70%]',
        isUser ? 'items-end' : 'items-start'
      )}>
        <div className={cn(
          'rounded-lg px-4 py-2 wrap-break-words',
          isUser
            ? 'bg-blue-500 text-white'
            : isCriticalAssistant
              ? 'bg-red-100 text-red-950 border border-red-300'
              : 'bg-gray-100 text-gray-900'
        )}>
          {isCriticalAssistant && (
            <p className="text-xs font-bold uppercase mb-1">Critical Alert</p>
          )}
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          {isCriticalAssistant && (phone || mapsUrl) && (
            <div className="mt-3 flex gap-2 flex-wrap">
              {phone && (
                <Button asChild size="sm" className="bg-red-600 hover:bg-red-700">
                  <a href={`tel:${phone}`}>
                    <PhoneCall className="w-4 h-4 mr-2" />
                    Call Now
                  </a>
                </Button>
              )}
              {mapsUrl && (
                <Button asChild size="sm" variant="outline">
                  <a href={mapsUrl} target="_blank" rel="noreferrer">
                    <ExternalLink className="w-4 h-4 mr-2" />
                    Nearby Hospitals
                  </a>
                </Button>
              )}
              {phone && (
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={async () => {
                    try {
                      await navigator.clipboard.writeText(phone);
                    } catch {
                      // No-op fallback if clipboard API is unavailable.
                    }
                  }}
                >
                  <Copy className="w-4 h-4 mr-2" />
                  Copy Number
                </Button>
              )}
            </div>
          )}
        </div>
        <span className="text-xs text-gray-500 mt-1">
          {timeLabel}
        </span>
      </div>
    </div>
  );
}
