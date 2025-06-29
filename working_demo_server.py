#!/usr/bin/env python3
"""
Simple RAG Chatbot Demo Server
A minimal FastAPI server to test the RAG chatbot functionality
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import json
from datetime import datetime

app = FastAPI(
    title="RAG Chatbot Demo",
    description="Simple demo server for testing RAG chatbot functionality",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatRequest(BaseModel):
    message: str
    include_context: bool = True
    max_context: int = 3

class ChatResponse(BaseModel):
    response: str
    language: str
    sources: List[dict]
    context_used: bool
    confidence: float

# Mock data
mock_documents = [
    {
        "id": "doc1",
        "filename": "services.json",
        "content": "Digital transformation services, cloud integration, data analytics",
        "language": "en"
    },
    {
        "id": "doc2", 
        "filename": "training.md",
        "content": "Training programs for AI, machine learning, and data science",
        "language": "en"
    }
]

@app.get("/")
async def root():
    """Welcome message"""
    return {
        "message": "🤖 RAG Chatbot Demo Server",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/v1/chat",
            "upload": "/api/v1/upload",
            "documents": "/api/v1/documents",
            "health": "/api/v1/health"
        }
    }

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Simple chat endpoint with mock responses"""
    
    # Auto-detect language
    language = "ar" if any('\u0600' <= char <= '\u06FF' for char in request.message) else "en"
    
    # Mock context search
    relevant_docs = []
    if request.include_context and any(word in request.message.lower() for word in ["service", "training", "help"]):
        relevant_docs = [
            {
                "filename": "services.json",
                "type": "json",
                "relevance": 0.85,
                "content_preview": "Digital transformation services..."
            }
        ]
    
    # Generate response based on language
    if language == "ar":
        response_text = f"أفهم سؤالك: '{request.message}'. يمكنني مساعدتك بالخدمات الرقمية والتدريب."
    else:
        response_text = f"I understand your question: '{request.message}'. I can help with digital services and training."
    
    return ChatResponse(
        response=response_text,
        language=language,
        sources=relevant_docs,
        context_used=len(relevant_docs) > 0,
        confidence=0.8
    )

@app.post("/api/v1/upload")
async def upload_document(file: UploadFile = File(...), category: str = "general"):
    """Mock document upload"""
    
    # Validate file type
    allowed_types = {'.pdf', '.md', '.markdown', '.txt', '.json'}
    file_ext = file.filename.split('.')[-1].lower()
    
    if f'.{file_ext}' not in allowed_types:
        raise HTTPException(400, f"Unsupported file type: .{file_ext}")
    
    # Mock processing
    content = await file.read()
    
    return {
        "success": True,
        "document_id": f"doc_{len(mock_documents) + 1}",
        "filename": file.filename,
        "file_type": file_ext,
        "chunks": 5,
        "language": "en"
    }

@app.get("/api/v1/documents")
async def list_documents():
    """List mock documents"""
    return [
        {
            "id": doc["id"],
            "filename": doc["filename"],
            "file_type": doc["filename"].split('.')[-1],
            "language": doc["language"],
            "chunks": 5,
            "uploaded_at": datetime.now().isoformat()
        }
        for doc in mock_documents
    ]

@app.delete("/api/v1/documents/{document_id}")
async def delete_document(document_id: str):
    """Mock document deletion"""
    return {"success": True, "message": f"Document {document_id} deleted"}

@app.get("/api/v1/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "RAG Chatbot Demo",
        "version": "1.0.0",
        "features": {
            "rag_chat": True,
            "document_upload": True,
            "language_detection": True,
            "supported_formats": [".pdf", ".md", ".txt", ".json"],
            "supported_languages": ["en", "ar", "fr"]
        },
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🚀 Starting RAG Chatbot Demo Server...")
    print("📖 API Documentation: http://localhost:8001/docs")
    print("🏠 Home: http://localhost:8001")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    ) 