import { RagWorkspace } from '@/components/rag/RagWorkspace';

export default function RagPage() {
  return (
    <div className="container mx-auto p-6 max-w-5xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">RAG Report Assistant</h1>
        <p className="text-gray-600">
          Upload your own medical PDF, store it in your knowledge base, and ask grounded questions with citations.
        </p>
      </div>

      <RagWorkspace />
    </div>
  );
}
