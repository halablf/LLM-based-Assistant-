"""
Simple RAG Chatbot API v1
"""

from fastapi import APIRouter
from .chat import router as chat_router

api_router = APIRouter()

# Include only the chat router
api_router.include_router(chat_router, prefix="", tags=["RAG Chatbot"]) 