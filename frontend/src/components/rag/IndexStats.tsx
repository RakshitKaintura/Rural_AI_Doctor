'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Database, FileText, RefreshCw, Layers, AlertCircle } from 'lucide-react';
import { ragAPI, IndexStats as IIndexStats } from '@/lib/api/rag';
import { Button } from '@/components/ui/button';

export function IndexStats() {
  const [stats, setStats] = useState<IIndexStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await ragAPI.getStats();
      
      if (data) {
        setStats(data);
      } else {
        throw new Error("No data received from engine");
      }
    } catch (err: any) {
      console.error('Failed to load stats:', err);
      setError(err.message === "Network Error" 
        ? "Backend Offline: Cannot connect to Port 8000" 
        : "Failed to sync knowledge base");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  if (loading && !stats) {
    return (
      <Card className="p-6 border-slate-200 shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <Database className="w-5 h-5 text-slate-300 animate-pulse" />
          <div className="h-5 bg-slate-100 rounded w-1/3 animate-pulse"></div>
        </div>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="h-20 bg-slate-50 rounded-xl animate-pulse"></div>
          <div className="h-20 bg-slate-50 rounded-xl animate-pulse"></div>
        </div>
        <div className="space-y-2">
          <div className="h-3 bg-slate-50 rounded w-1/4 animate-pulse"></div>
          <div className="h-8 bg-slate-50 rounded animate-pulse"></div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6 border-red-100 bg-red-50 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-6 h-6 text-red-500" />
            <div>
              <h3 className="text-sm font-bold text-red-800 uppercase tracking-tight">Sync Failed</h3>
              <p className="text-xs text-red-600 font-medium">{error}</p>
            </div>
          </div>
          <Button 
            size="sm" 
            variant="outline" 
            onClick={loadStats}
            className="bg-white border-red-200 text-red-700 hover:bg-red-50"
          >
            <RefreshCw className="w-3 h-3 mr-2" />
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6 border-slate-200 shadow-sm bg-white">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-blue-50 rounded-lg">
            <Database className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-800">Knowledge Base Statistics</h3>
            <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">Vector Index Status</p>
          </div>
        </div>
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={loadStats}
          disabled={loading}
          className="hover:bg-slate-100 text-slate-400 hover:text-blue-600 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-blue-50/50 border border-blue-100 rounded-xl">
            <div className="flex items-center gap-2 mb-2 text-blue-700">
              <Layers className="w-4 h-4" />
              <p className="text-[11px] font-bold uppercase">Total Chunks</p>
            </div>
            <p className="text-3xl font-black text-blue-600 tracking-tight">
              {(stats?.total_chunks ?? 0).toLocaleString()}
            </p>
            <p className="text-[10px] text-blue-500/70 font-medium mt-1">Searchable segments</p>
          </div>
          
          <div className="p-4 bg-emerald-50/50 border border-emerald-100 rounded-xl">
            <div className="flex items-center gap-2 mb-2 text-emerald-700">
              <FileText className="w-4 h-4" />
              <p className="text-[11px] font-bold uppercase">Documents</p>
            </div>
            <p className="text-3xl font-black text-emerald-600 tracking-tight">
              {/* FIX: Fallback to sources.length if unique_sources is 0 or missing.
                  This ensures the "0" becomes "1" in your specific case.
              */}
              {(stats?.unique_sources || stats?.sources?.length || 0).toLocaleString()}
            </p>
            <p className="text-[10px] text-emerald-500/70 font-medium mt-1">Unique medical files</p>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-bold text-slate-700 uppercase tracking-tight">Indexed Sources</p>
            <span className="text-[10px] font-medium text-slate-400">
              Total: {stats?.sources?.length ?? 0}
            </span>
          </div>
          
          <div className="bg-slate-50 border border-slate-100 rounded-xl p-3 min-h-25">
            {stats?.sources && stats.sources.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {stats.sources.map((source, idx) => (
                  <Badge 
                    key={idx} 
                    variant="secondary" 
                    className="bg-white border-slate-200 text-slate-600 hover:border-blue-300 hover:text-blue-600 transition-all px-2 py-1 flex items-center gap-1.5 text-[11px] font-medium shadow-sm"
                  >
                    <FileText className="w-3 h-3 text-slate-400" />
                    {source}
                  </Badge>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full py-4 text-slate-400">
                <FileText className="w-8 h-8 opacity-20 mb-2" />
                <p className="text-xs italic">No documents indexed yet.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}