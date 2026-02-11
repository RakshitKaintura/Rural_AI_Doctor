'use client';

import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, Loader2, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ragAPI } from '@/lib/api/rag';

export function DocumentUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.type !== 'application/pdf') {
        setStatus('error');
        setMessage('Please upload a PDF file.');
        return;
      }
      setFile(selectedFile);
      setStatus('idle');
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    try {
      setStatus('uploading');
      await ragAPI.uploadFile(file);
      setStatus('success');
      setMessage(`${file.name} indexed successfully.`);
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (error) {
      setStatus('error');
      setMessage('Upload failed. Check backend connection.');
    }
  };

  return (
    <Card className="p-6 border-slate-200 shadow-sm bg-white" suppressHydrationWarning>
      <div className="flex items-center gap-2 mb-6">
        <div className="p-2 bg-blue-50 rounded-lg">
          <Upload className="w-5 h-5 text-blue-600" />
        </div>
        <div>
          <h3 className="text-base font-bold text-slate-800">Ingest Knowledge</h3>
          <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">PDF Processing Pipeline</p>
        </div>
      </div>

      <div 
        className={`relative border-2 border-dashed rounded-xl p-8 transition-all flex flex-col items-center justify-center gap-3
          ${file ? 'border-blue-400 bg-blue-50/30' : 'border-slate-200 hover:border-slate-300 bg-slate-50/50'}`}
      >
      
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".pdf"
          className="absolute inset-0 opacity-0 cursor-pointer"
          suppressHydrationWarning
        />

        {!file ? (
          <>
            <div className="p-3 bg-white rounded-full shadow-sm border border-slate-100">
              <FileText className="w-6 h-6 text-slate-400" />
            </div>
            <div className="text-center">
              <p className="text-sm font-semibold text-slate-700">Click or drag PDF</p>
              <p className="text-[11px] text-slate-400 mt-1">Maximum size: 10MB</p>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center animate-in fade-in zoom-in duration-300">
            <div className="p-3 bg-blue-600 rounded-full shadow-lg">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <p className="text-sm font-bold text-blue-700 mt-3 truncate max-w-50">
              {file.name}
            </p>
            <button 
              onClick={() => setFile(null)}
              className="mt-2 text-[10px] font-bold text-slate-400 hover:text-red-500 flex items-center gap-1 uppercase tracking-tighter"
            >
              <X className="w-3 h-3" /> Remove
            </button>
          </div>
        )}
      </div>

      {status !== 'idle' && (
        <div className={`mt-4 p-3 rounded-lg flex items-center gap-3 animate-in slide-in-from-top-2
          ${status === 'uploading' ? 'bg-slate-100 text-slate-600' : ''}
          ${status === 'success' ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' : ''}
          ${status === 'error' ? 'bg-red-50 text-red-700 border border-red-100' : ''}
        `}>
          {status === 'uploading' && <Loader2 className="w-4 h-4 animate-spin" />}
          {status === 'success' && <CheckCircle2 className="w-4 h-4" />}
          {status === 'error' && <AlertCircle className="w-4 h-4" />}
          <p className="text-xs font-medium">{message || 'Processing document...'}</p>
        </div>
      )}

      <Button
        onClick={handleUpload}
        disabled={!file || status === 'uploading'}
        className="w-full mt-6 bg-slate-900 hover:bg-blue-700 text-white font-bold py-6 rounded-xl transition-all shadow-lg shadow-slate-200 disabled:opacity-50"
      >
        {status === 'uploading' ? (
          <span className="flex items-center gap-2 text-xs uppercase tracking-widest">
            <Loader2 className="w-4 h-4 animate-spin" /> Vectorizing...
          </span>
        ) : (
          <span className="text-xs uppercase tracking-widest">Start Ingestion</span>
        )}
      </Button>
    </Card>
  );
}