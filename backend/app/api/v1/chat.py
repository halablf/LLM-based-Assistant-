"""
Simple RAG Chatbot API
Supports document upload (JSON/Markdown/PDF) and intelligent chat with language detection
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import asyncio
from datetime import datetime
from pathlib import Path

from ...services.pdf_processing_service import document_processing_service
from ...agents.retrieval import DocumentRetrievalAgent
from ...utils.logging import logger

router = APIRouter(tags=["🤖 RAG Chatbot"])

# Models
class ChatRequest(BaseModel):
    """Chat with RAG-enhanced context"""
    message: str = Field(..., description="User message", min_length=1, max_length=1000)
    include_context: bool = Field(True, description="Include document context")
    max_context: int = Field(3, description="Max context documents", ge=1, le=10)

class ChatResponse(BaseModel):
    """Chat response with sources"""
    response: str = Field(..., description="AI response")
    language: str = Field(..., description="Detected/response language")
    sources: List[Dict[str, Any]] = Field(..., description="Source documents")
    context_used: bool = Field(..., description="Whether context was used")
    confidence: float = Field(..., description="Response confidence")

class UploadResponse(BaseModel):
    """Document upload response"""
    success: bool = Field(..., description="Upload success")
    document_id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Filename")
    file_type: str = Field(..., description="File type")
    chunks: int = Field(..., description="Text chunks created")
    language: str = Field(..., description="Detected language")

class DocumentInfo(BaseModel):
    """Document information"""
    id: str
    filename: str
    file_type: str
    language: str
    chunks: int
    uploaded_at: str

# Initialize retrieval agent
retrieval_agent = DocumentRetrievalAgent()

# Supported file types
SUPPORTED_TYPES = {'.pdf', '.md', '.markdown', '.txt', '.json'}

@router.post("/chat", response_model=ChatResponse, summary="💬 Chat with RAG")
async def chat_with_rag(request: ChatRequest):
    """
    **Main RAG Chat Endpoint**
    
    Send a message and get an AI response enhanced with relevant document context.
    
    **Features:**
    - **Automatic language detection** from your message
    - **Document context retrieval** from uploaded files and database
    - **Multi-language responses** (EN/AR/FR)
    - **Source citations** showing which documents were used
    
    **Supported Languages:**
    - English (en) - Detected from Latin text
    - Arabic (ar) - Detected from Arabic script
    - French (fr) - Detected from French words/patterns
    """
    start_time = datetime.now()
    
    try:
        # Auto-detect language
        language = await _detect_language(request.message)
        logger.info(f"💬 Chat request: '{request.message[:50]}...' (language: {language})")
        
        # Get relevant context if requested
        context_chunks = []
        if request.include_context:
            context_chunks = await document_processing_service.search_documents(
                query=request.message,
                language=language,
                max_results=request.max_context
            )
        
        # Generate response based on context
        if context_chunks:
            response_text = await _generate_context_response(
                request.message, context_chunks, language
            )
            sources = [
                {
                    "filename": chunk.source_file,
                    "type": chunk.source_type,
                    "relevance": round(chunk.relevance_score, 3),
                    "content_preview": chunk.content[:100] + "..."
                }
                for chunk in context_chunks
            ]
            confidence = 0.85
            context_used = True
        else:
            response_text = await _generate_fallback_response(request.message, language)
            sources = []
            confidence = 0.4
            context_used = False
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"💬 Chat completed in {processing_time:.3f}s ({len(context_chunks)} contexts)")
        
        return ChatResponse(
            response=response_text,
            language=language,
            sources=sources,
            context_used=context_used,
            confidence=confidence
        )
        
    except Exception as e:
        logger.error(f"Chat failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.post("/upload", response_model=UploadResponse, summary="📤 Upload Document")
async def upload_document(
    file: UploadFile = File(..., description="Document file (PDF/Markdown/Text/JSON)"),
    category: str = Query("general", description="Document category")
):
    """
    **Upload Document for RAG**
    
    Upload documents to enhance the chatbot's knowledge base.
    
    **Supported Formats:**
    - **PDF**: Extracted text with page references
    - **Markdown**: Section-based parsing (.md, .markdown)
    - **Text**: Plain text files (.txt)
    - **JSON**: Structured data (.json)
    
    **Processing:**
    - Automatic language detection from content
    - Intelligent text chunking for better retrieval
    - Embedding generation for semantic search
    """
    try:
        # Validate file type
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in SUPPORTED_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Supported: {', '.join(SUPPORTED_TYPES)}"
            )
        
        # Check file size (10MB limit for simplicity)
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 10MB)")
        
        logger.info(f"📤 Uploading: {file.filename} ({len(file_content)} bytes)")
        
        # Process document
        result = await document_processing_service.upload_and_process_file(
            file_content, file.filename, category, "auto"
        )
        
        if result.success:
            return UploadResponse(
                success=True,
                document_id=result.document_id,
                filename=result.file_name,
                file_type=result.file_type,
                chunks=result.total_chunks,
                language=result.language_detected
            )
        else:
            raise HTTPException(status_code=422, detail=result.error_message)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/documents", response_model=List[DocumentInfo], summary="📋 List Documents")
async def list_documents():
    """
    **List Uploaded Documents**
    
    Get a list of all uploaded documents in the knowledge base.
    """
    try:
        documents = []
        for doc_id, doc_info in document_processing_service.document_index.get("documents", {}).items():
            documents.append(DocumentInfo(
                id=doc_id,
                filename=doc_info["filename"],
                file_type=doc_info["file_type"],
                language=doc_info["language"],
                chunks=doc_info["total_chunks"],
                uploaded_at=doc_info["created_at"]
            ))
        
        return documents
        
    except Exception as e:
        logger.error(f"List documents failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list documents")

@router.delete("/documents/{document_id}", summary="🗑️ Delete Document")
async def delete_document(document_id: str):
    """
    **Delete Document**
    
    Remove a document from the knowledge base.
    """
    try:
        if document_id not in document_processing_service.document_index.get("documents", {}):
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete chunks file
        chunks_file = document_processing_service.embeddings_dir / f"{document_id}_chunks.json"
        if chunks_file.exists():
            chunks_file.unlink()
        
        # Remove from index
        del document_processing_service.document_index["documents"][document_id]
        document_processing_service._save_document_index()
        
        return {"success": True, "message": f"Document {document_id} deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Delete failed")

@router.get("/health", summary="💓 Health Check")
async def health_check():
    """
    **System Health Check**
    
    Check if the RAG chatbot is running properly.
    """
    return {
        "status": "healthy",
        "service": "RAG Chatbot",
        "version": "1.0.0",
        "features": {
            "rag_chat": True,
            "document_upload": True,
            "language_detection": True,
            "supported_formats": list(SUPPORTED_TYPES),
            "supported_languages": ["en", "ar", "fr"]
        },
        "timestamp": datetime.now().isoformat()
    }

# Helper functions
async def _detect_language(text: str) -> str:
    """Auto-detect language from text"""
    text_sample = text[:500].lower()
    
    # Count Arabic characters
    arabic_chars = sum(1 for char in text_sample if '\u0600' <= char <= '\u06FF')
    
    # Common French words
    french_words = ['le', 'la', 'les', 'un', 'une', 'des', 'et', 'avec', 'pour', 'dans', 'comment', 'que']
    french_count = sum(1 for word in french_words if word in text_sample)
    
    if arabic_chars > 3:
        return "ar"
    elif french_count > 1:
        return "fr"
    else:
        return "en"

async def _generate_context_response(message: str, chunks: list, language: str) -> str:
    """Generate response with document context"""
    context_text = "\n\n".join([
        f"From {chunk.source_file}: {chunk.content[:200]}..."
        for chunk in chunks[:2]
    ])
    
    templates = {
        "en": f"Based on the available documents, I can help with your question: '{message}'\n\nRelevant information:\n{context_text}\n\nHow can I assist you further?",
        "ar": f"بناءً على الوثائق المتاحة، يمكنني مساعدتك في سؤالك: '{message}'\n\nمعلومات ذات صلة:\n{context_text}\n\nكيف يمكنني مساعدتك أكثر؟",
        "fr": f"Basé sur les documents disponibles, je peux vous aider avec votre question: '{message}'\n\nInformations pertinentes:\n{context_text}\n\nComment puis-je vous aider davantage?"
    }
    
    return templates.get(language, templates["en"])

async def _generate_fallback_response(message: str, language: str) -> str:
    """Generate fallback response without context"""
    templates = {
        "en": f"I understand your question: '{message}'. I don't have specific information in my current knowledge base, but I'm here to help. Could you provide more details or upload relevant documents?",
        "ar": f"أفهم سؤالك: '{message}'. لا أملك معلومات محددة في قاعدة المعرفة الحالية، لكنني هنا للمساعدة. هل يمكنك تقديم تفاصيل أكثر أو رفع وثائق ذات صلة؟",
        "fr": f"Je comprends votre question: '{message}'. Je n'ai pas d'informations spécifiques dans ma base de connaissances actuelle, mais je suis là pour aider. Pourriez-vous fournir plus de détails ou télécharger des documents pertinents?"
    }
    
    return templates.get(language, templates["en"]) 