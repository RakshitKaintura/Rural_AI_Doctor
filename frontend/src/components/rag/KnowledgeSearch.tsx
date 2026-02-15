'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Search, FileText, Loader2, BookOpen, AlertCircle, XCircle } from 'lucide-react';
import { ragAPI, RAGQueryResponse } from '@/lib/api/rag';
import axios from 'axios';

export function KnowledgeSearch() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RAGQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!question.trim()) return;

    try {
      setLoading(true);
      setError(null);
 
      const data = await ragAPI.query(String(question), 5);
      setResult(data);
      
    } catch (err: any) {
      console.error("Search Error:", err);
      
      if (axios.isAxiosError(err) && err.response?.status === 422) {
        const details = err.response.data.detail;
       
        const formattedError = Array.isArray(details) 
          ? details.map((e: any) => `${e.loc[e.loc.length - 1]}: ${e.msg}`).join(', ')
          : "Invalid request format sent to server.";
        
        setError(formattedError);
      } else {
        setError(err.message || "An unexpected error occurred while searching.");
      }
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  return (
    <div className="space-y-4">
      {/* Search Bar Section */}
      <Card className="p-4 border-slate-200 shadow-sm">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <BookOpen className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a medical question (e.g., 'What is the treatment for pneumonia?')"
              disabled={loading}
              className="pl-10 h-11 bg-slate-50 border-slate-200 focus:bg-white transition-all shadow-none"
            />
          </div>
          <Button 
            onClick={handleSearch} 
            disabled={loading || !question.trim()}
            className="h-11 px-6 bg-blue-600 hover:bg-blue-700 transition-colors shrink-0"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <Search className="w-4 h-4 mr-2" />
                Search
              </>
            )}
          </Button>
        </div>
        <p className="text-[11px] text-slate-500 mt-2 flex items-center gap-1 font-medium">
          <span className="w-1 h-1 bg-slate-400 rounded-full" />
          Press Enter to search • Answers are grounded in your uploaded clinical guidelines
        </p>
      </Card>

      {/* Error Feedback Section */}
      {error && (
        <Card className="p-4 border-red-200 bg-red-50 flex items-start gap-3 animate-in fade-in zoom-in duration-200">
          <XCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-sm font-bold text-red-900">Search Failed</h4>
            <p className="text-xs text-red-700 leading-relaxed font-medium">{error}</p>
          </div>
        </Card>
      )}

      {/* RAG Result Rendering */}
      {result && (
        <div className="space-y-4 animate-in fade-in slide-in-from-top-4 duration-300">
          {/* Main AI Answer Card */}
          <Card className="p-6 border-slate-200 shadow-md bg-white">
            <div className="flex items-start gap-3 mb-5">
              <div className="p-2.5 bg-blue-50 rounded-xl border border-blue-100">
                <BookOpen className="w-5 h-5 text-blue-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-slate-800">Clinical Answer</h3>
                <p className="text-xs font-semibold text-blue-600 uppercase tracking-wider">
                  Verified Knowledge Base Response
                </p>
              </div>
            </div>
            
            {/* Scrollable area for deep clinical responses */}
            <ScrollArea className="max-h-[600px] pr-4">
              <div className="text-slate-700 whitespace-pre-wrap leading-relaxed pb-6 text-base">
                {result.answer}
              </div>
            </ScrollArea>
          </Card>

          {/* Citation / Source Evidence Section */}
          {result.sources && result.sources.length > 0 && (
            <Card className="p-6 border-slate-200 shadow-sm bg-slate-50/50">
              <h3 className="text-sm font-bold text-slate-500 mb-4 flex items-center gap-2 uppercase tracking-tight">
                <FileText className="w-4 h-4" />
                Supporting Documentation ({result.sources.length})
              </h3>
              <div className="grid grid-cols-1 gap-3">
                {result.sources.map((source, idx) => (
                  <div
                    key={source.id || idx}
                    className="p-4 bg-white border border-slate-200 rounded-xl hover:border-blue-300 hover:shadow-sm transition-all group"
                  >
                    <div className="flex items-start gap-4">
                      <div className="shrink-0 w-8 h-8 bg-slate-100 rounded-lg flex items-center justify-center group-hover:bg-blue-600 group-hover:text-white transition-colors">
                        <span className="text-xs font-bold">{idx + 1}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <h4 className="font-bold text-sm text-slate-800 truncate">
                            {source.title}
                          </h4>
                          <Badge variant="outline" className="shrink-0 bg-blue-50 text-blue-700 border-blue-200 text-[10px] font-bold">
                            {(source.similarity * 100).toFixed(0)}% Semantic Match
                          </Badge>
                        </div>
                        <p className="text-xs text-slate-600 leading-normal mb-3 line-clamp-3 italic bg-slate-50 p-2 rounded-md border-l-2 border-slate-300">
                          "{source.text}"
                        </p>
                        {source.metadata?.uploaded_filename && (
                          <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase">
                            <FileText className="w-3 h-3" />
                            <span>{source.metadata.uploaded_filename}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          
          {(!result.sources || result.sources.length === 0) && (
            <Card className="p-4 bg-amber-50 border-amber-200 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-amber-600 shrink-0" />
              <p className="text-xs font-semibold text-amber-800">
                WARNING: No source documents were retrieved. This answer is based on general AI knowledge.
              </p>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}