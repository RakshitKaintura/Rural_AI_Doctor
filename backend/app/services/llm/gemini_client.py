from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.core.config import settings
from typing import List, Dict, Type, TypeVar
import os
from google import genai

T = TypeVar("T")

class GeminiClient:
    def __init__(self):

        if settings.GOOGLE_API_KEY:
            os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
        
        self.llm = ChatGoogleGenerativeAI(
        model="gemini-3.0-flash", 
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.1,
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
        """Standard text generation."""
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content

    async def generate_structured(self, prompt: str, response_model: Type[T]) -> T:
        """
        Generates a structured response mapped to a Pydantic model.
        This fixes the AttributeError in the agent nodes.
        """
       
        structured_llm = self.llm.with_structured_output(response_model)
        

        response = await structured_llm.ainvoke([HumanMessage(content=prompt)])
        
        return response

gemini_client = GeminiClient()