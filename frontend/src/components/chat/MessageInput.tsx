import { useState, KeyboardEvent } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ImagePlus, Mic, Send, X } from 'lucide-react';

interface MessageInputProps {
  onSend: (payload: { content: string; imageFile?: File | null; audioFile?: File | null }) => void;
  disabled: boolean;
}

export function MessageInput({ onSend, disabled }: MessageInputProps) {
  const [input, setInput] = useState('');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);

  const handleSend = () => {
    if ((input.trim() || imageFile || audioFile) && !disabled) {
      onSend({ content: input.trim(), imageFile, audioFile });
      setInput('');
      setImageFile(null);
      setAudioFile(null);
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t p-4 bg-white">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <label className="inline-flex items-center">
          <input
            type="file"
            accept="image/*"
            className="hidden"
            disabled={disabled}
            onChange={(e) => setImageFile(e.target.files?.[0] ?? null)}
          />
          <span className="inline-flex cursor-pointer items-center rounded-md border px-2 py-1 text-xs text-gray-700 hover:bg-gray-50">
            <ImagePlus className="mr-1 h-3.5 w-3.5" />
            Add Image
          </span>
        </label>
        <label className="inline-flex items-center">
          <input
            type="file"
            accept="audio/*"
            className="hidden"
            disabled={disabled}
            onChange={(e) => setAudioFile(e.target.files?.[0] ?? null)}
          />
          <span className="inline-flex cursor-pointer items-center rounded-md border px-2 py-1 text-xs text-gray-700 hover:bg-gray-50">
            <Mic className="mr-1 h-3.5 w-3.5" />
            Add Audio
          </span>
        </label>
      </div>

      {(imageFile || audioFile) && (
        <div className="mb-2 flex flex-wrap gap-2">
          {imageFile && (
            <div className="inline-flex items-center gap-1 rounded-full border bg-gray-50 px-2 py-1 text-xs text-gray-700">
              <span>{imageFile.name}</span>
              <button type="button" onClick={() => setImageFile(null)} disabled={disabled} aria-label="Remove image">
                <X className="h-3 w-3" />
              </button>
            </div>
          )}
          {audioFile && (
            <div className="inline-flex items-center gap-1 rounded-full border bg-gray-50 px-2 py-1 text-xs text-gray-700">
              <span>{audioFile.name}</span>
              <button type="button" onClick={() => setAudioFile(null)} disabled={disabled} aria-label="Remove audio">
                <X className="h-3 w-3" />
              </button>
            </div>
          )}
        </div>
      )}

      <div className="flex gap-2">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Describe your symptoms..."
          className="resize-none"
          rows={3}
          disabled={disabled}
        />
        <Button
          onClick={handleSend}
          disabled={disabled || (!input.trim() && !imageFile && !audioFile)}
          size="icon"
          className="self-end"
        >
          <Send className="w-4 h-4" />
        </Button>
      </div>
      <p className="text-xs text-gray-500 mt-2">
        Press Enter to send, Shift+Enter for new line. You can also attach one image and one audio file.
      </p>
    </div>
  );
}
