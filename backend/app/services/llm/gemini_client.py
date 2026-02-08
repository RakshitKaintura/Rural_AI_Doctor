from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.core.config import settings
from typing import List, Dict
import os

class GeminiClient:
    def __init__(self):
        # Set API Key
        # Ensure your settings has GOOGLE_API_KEY from .env
        if settings.GOOGLE_API_KEY:
            os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3,
            max_output_tokens=2048,
        )
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = None
    ) -> str:
        lc_messages = []
        
        if system_prompt:
            lc_messages.append(SystemMessage(content=system_prompt))
        
        for msg in messages:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
        
        response = await self.llm.ainvoke(lc_messages)
        return response.content
    
    async def generate(self, prompt: str) -> str:
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content

# Singleton instance
gemini_client = GeminiClient()