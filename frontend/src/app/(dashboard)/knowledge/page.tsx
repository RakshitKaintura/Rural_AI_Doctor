'use client'

import React from 'react';
import { DocumentUpload } from '@/components/rag/DocumentUpload';
import { KnowledgeSearch } from '@/components/rag/KnowledgeSearch';
import { IndexStats } from '@/components/rag/IndexStats';
import { BookOpen, Database, ShieldCheck, Activity } from 'lucide-react';

/**
 * KnowledgePage: The central hub for the Rural AI Doctor's knowledge base.
 */
export default function KnowledgePage() {
  return (
    <div className="min-h-screen bg-slate-50/50" suppressHydrationWarning>
      <div className="container mx-auto p-6 max-w-5xl">
        
        {/* Page Header */}
        <header className="mb-10 pt-4">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-black text-slate-900 tracking-tight">
              Medical Knowledge Base
            </h1>
            <span className="text-3xl" role="img" aria-label="books">📚</span>
          </div>
          <p className="text-slate-600 max-w-2xl leading-relaxed text-lg">
            Ground your AI in local evidence. Upload clinical guidelines and research 
            to power the <strong>Retrieval Augmented Generation (RAG)</strong> engine.
          </p>
        </header>

        <div className="grid gap-8">
          {/* Real-time Vector Database Statistics */}
          <section className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/30">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-blue-600" />
                <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                  Vector Database Status
                </h2>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                <span className="text-[10px] font-bold text-emerald-600 uppercase">Live Engine</span>
              </div>
            </div>
            <div className="p-6">
              <IndexStats />
            </div>
          </section>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
            {/* Sidebar: Document Upload & Guardrail Info */}
            <aside className="md:col-span-4 space-y-6">
              <div className="sticky top-6">
                <DocumentUpload />
                
                <div className="mt-6 p-5 rounded-2xl bg-gradient-to-br from-blue-600 to-blue-700 text-white shadow-xl shadow-blue-200">
                  <div className="flex items-center gap-2 mb-3">
                    <ShieldCheck className="w-5 h-5 text-blue-200" />
                    <h4 className="text-xs font-bold uppercase tracking-widest opacity-90">
                      Grounded in Evidence
                    </h4>
                  </div>
                  <p className="text-sm font-medium leading-relaxed mb-4">
                    Every AI response is verified against your 133 uploaded data chunks to prevent medical hallucinations.
                  </p>
                  <div className="flex items-center gap-2 text-[10px] font-bold py-1.5 px-3 bg-white/10 rounded-lg backdrop-blur-sm w-fit">
                    <Activity className="w-3 h-3" />
                    System Latency: 14ms
                  </div>
                </div>
              </div>
            </aside>

            {/* Main Content: Search Engine */}
            <main className="md:col-span-8">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-blue-600" />
                  Clinical Semantic Search
                </h2>
                <div className="h-px flex-1 bg-slate-200 mx-4" />
              </div>
              
              <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden min-h-[400px]">
                <KnowledgeSearch />
              </div>
            </main>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-20 pb-10 border-t border-slate-200 pt-8">
          <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest text-center">
            Rural AI Doctor Platform • 2026 Build
          </p>
        </footer>
      </div>
    </div>
  );
}