"""
Simple LLM Service for RAG Chatbot - OpenAI integration
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from openai import AsyncOpenAI
import json
import os

from ..utils.logging import get_logger

logger = get_logger(__name__)

# Simple config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
SUPPORTED_LANGUAGES = ["en", "ar", "fr"]


class LLMService:
    """Service for handling LLM interactions with OpenAI."""
    
    def __init__(self):
        if not OPENAI_API_KEY:
            logger.warning("OpenAI API key not provided - LLM features will be limited")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        self.model = OPENAI_MODEL
        self.max_tokens = OPENAI_MAX_TOKENS
        self.temperature = OPENAI_TEMPERATURE
        
        logger.info(f"🤖 LLM Service initialized with model: {self.model}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the OpenAI API connection."""
        if not self.client:
            return {
                "status": "error",
                "error": "OpenAI API key not configured",
                "model": self.model
            }
        
        try:
            logger.info("Testing OpenAI API connection...")
            start_time = time.time()
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Hello from RAG Chatbot!'"}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            duration = time.time() - start_time
            response_text = response.choices[0].message.content
            
            result = {
                "status": "success",
                "model": self.model,
                "response": response_text,
                "tokens_used": response.usage.total_tokens,
                "duration_seconds": round(duration, 2)
            }
            
            logger.info(f"✅ OpenAI API test successful - {result['duration_seconds']}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ OpenAI API test failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "model": self.model
            }
    
    async def generate_response(
        self,
        message: str,
        system_prompt: str = "",
        language: str = "en",
        temperature: Optional[float] = None
    ) -> str:
        """Generate a simple response using OpenAI."""
        if not self.client:
            # Return a mock response if no OpenAI key
            return f"I understand your message: '{message}'. (Note: OpenAI not configured, this is a mock response)"
        
        try:
            messages = []
            
            # Add system prompt if provided
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            else:
                # Default system prompt based on language
                default_prompts = {
                    "en": "You are a helpful AI assistant. Respond clearly and professionally.",
                    "ar": "أنت مساعد ذكي مفيد. استجب بوضوح وباحترافية.",
                    "fr": "Vous êtes un assistant IA utile. Répondez clairement et professionnellement."
                }
                messages.append({"role": "system", "content": default_prompts.get(language, default_prompts["en"])})
            
            # Add user message
            messages.append({"role": "user", "content": message})
            
            logger.info(f"🤖 Generating response for: '{message[:50]}...' (language: {language})")
            start_time = time.time()
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=temperature or self.temperature
            )
            
            duration = time.time() - start_time
            response_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            logger.info(f"✅ Response generated ({tokens_used} tokens, {duration:.2f}s)")
            return response_text
                
        except Exception as e:
            logger.error(f"❌ Failed to generate response: {str(e)}")
            # Return fallback response
            return f"I apologize, but I'm having trouble processing your request right now. Please try again later."
    
    async def detect_language(self, text: str) -> str:
        """Simple language detection (fallback to pattern matching if no OpenAI)."""
        if not self.client:
            # Simple pattern-based detection
            text_lower = text[:200].lower()
            
            # Count Arabic characters
            arabic_chars = sum(1 for char in text_lower if '\u0600' <= char <= '\u06FF')
            
            # Common French words
            french_words = ['le', 'la', 'les', 'un', 'une', 'des', 'et', 'avec', 'pour']
            french_count = sum(1 for word in french_words if word in text_lower)
            
            if arabic_chars > 3:
                return "ar"
            elif french_count > 1:
                return "fr"
            else:
                return "en"
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "Detect the language of the following text. Respond with only the ISO 639-1 code (en, ar, fr)."
                    },
                    {"role": "user", "content": text[:200]}  # Limit text for efficiency
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            detected_language = response.choices[0].message.content.strip().lower()
            
            if detected_language in SUPPORTED_LANGUAGES:
                return detected_language
            else:
                logger.warning(f"Unknown language detected: {detected_language}, defaulting to en")
                return "en"
                
        except Exception as e:
            logger.error(f"Language detection failed: {str(e)}")
            return "en"  # Default to English


# Global service instance
llm_service = LLMService()

# Convenience functions
async def generate_response(message: str, language: str = "en", system_prompt: str = "") -> str:
    """Generate a response using the global LLM service."""
    return await llm_service.generate_response(message, system_prompt, language)

async def test_llm_connection() -> Dict[str, Any]:
    """Test the LLM connection."""
    return await llm_service.test_connection() 