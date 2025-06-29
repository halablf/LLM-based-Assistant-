"""
Simple RAG Chatbot Backend
A clean, minimal AI assistant with document upload and intelligent responses
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import os
from datetime import datetime

from .api.v1 import api_router
from .utils.logging import logger

# Application metadata
APP_NAME = "RAG Chatbot API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = """
🤖 **Simple RAG Chatbot API**

A clean, minimal AI assistant that can:

- **Chat with context** from uploaded documents
- **Upload documents** (PDF, Markdown, Text, JSON)
- **Auto-detect language** and respond accordingly (EN/AR/FR)
- **Search documents** for relevant information

Perfect for university projects and simple AI applications.
"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events"""
    
    # Startup
    logger.info(f"🚀 Starting {APP_NAME} v{APP_VERSION}")
    logger.info("✅ RAG Chatbot ready for requests")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down RAG Chatbot")

# Create FastAPI app
app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Root endpoint
@app.get("/", tags=["🏠 Home"])
async def root():
    """
    **RAG Chatbot API Home**
    
    Welcome to the simple RAG (Retrieval Augmented Generation) chatbot API.
    """
    return {
        "message": "🤖 Welcome to RAG Chatbot API",
        "version": APP_VERSION,
        "features": [
            "💬 Intelligent chat with document context",
            "📤 Multi-format document upload (PDF/Markdown/Text/JSON)",
            "🌍 Auto language detection (EN/AR/FR)",
            "🔍 Document search and retrieval"
        ],
        "endpoints": {
            "chat": "/api/v1/chat",
            "upload": "/api/v1/upload", 
            "documents": "/api/v1/documents",
            "health": "/api/v1/health",
            "docs": "/docs"
        },
        "timestamp": datetime.now().isoformat()
    }

# Health check
@app.get("/health", tags=["💓 Health"])
async def global_health():
    """Global health check endpoint"""
    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "message": "The requested endpoint doesn't exist",
            "available_endpoints": [
                "/api/v1/chat",
                "/api/v1/upload",
                "/api/v1/documents",
                "/api/v1/health",
                "/docs"
            ]
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    logger.error(f"Internal server error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
        log_level="info"
    ) 