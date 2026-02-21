import psycopg
from google import genai
from google.genai import types
from app.services.rag.embeddings import embedding_service
from app.core.config import settings
client = genai.Client(api_key=settings.GOOGLE_API_KEY)

class RAGService:
    def __init__(self):
        self.db_url = settings.DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
        self.model_id = "gemini-2.5-flash-lite"

    def get_context(self, query_vector: list):
        """
        Retrieves the most relevant medical chunk using Vector Similarity Search.
        Uses the <-> operator for Euclidean distance or <=> for Cosine similarity.
        """
        try:
            with psycopg.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT content, title FROM medical_documents
                        ORDER BY embedding <=> %s::vector 
                        LIMIT %s;
                    """, (query_vector, settings.TOP_K_RESULTS))
                    
                    rows = cur.fetchall()
                    if not rows:
                        return None, None
                    
                    combined_context = "\n\n".join([row[0] for row in rows])
                    sources = ", ".join(list(set([row[1] for row in rows])))
                    return combined_context, sources
        except Exception as e:
            print(f" Database Retrieval Error: {e}")
            return None, None

    async def answer_question(self, user_query: str):
        """
        The core RAG Pipeline: 
        1. Query -> Embedding
        2. Embedding -> Vector Search (Context)
        3. Context + Query -> Gemini 2.5-Flash-Lite
        """

        vector = embedding_service.embed_query(user_query)
        
        context_text, source_titles = self.get_context(vector)
        
        if not context_text:
            return "I'm sorry, I don't have enough information in my medical database to answer that accurately. Please consult a doctor."

        prompt = f"""
        ROLE: You are an expert Rural Doctor AI.
        STRICT RULE: Answer the question using ONLY the provided medical context.
        If the answer isn't there, say you don't know and advise a clinic visit.

        MEDICAL CONTEXT (Sources: {source_titles}):
        {context_text}

        PATIENT QUESTION: 
        {user_query}

        INSTRUCTIONS:
        - Be empathetic and clear.
        - Use bullet points for symptoms or steps.
        - Mention that your information comes from: {source_titles}.

        DOCTOR AI RESPONSE:
        """

        try:
            response = client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,  # Keep it very factual
                    max_output_tokens=1000
                )
            )
            return response.text
        except Exception as e:
            return f"I encountered an error while processing your request: {str(e)}"

rag_service = RAGService()