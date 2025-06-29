"""
Document Processing Service - RAG-based document processing for PDF and Markdown files
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import re

# PDF Processing imports (optional dependencies)
try:
    import PyPDF2
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# ML/AI imports (optional dependencies)
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

# Image processing for OCR fallback
try:
    import pytesseract
    from PIL import Image
    import cv2
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Markdown processing
try:
    import markdown
    from markdown.extensions import codehilite, toc
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

from ..utils.logging import logger

@dataclass
class DocumentChunk:
    """Represents a processed document chunk with metadata"""
    id: str
    content: str
    source_file: str
    source_type: str  # "pdf", "markdown", "json", "text"
    page_number: Optional[int]
    chunk_index: int
    language: str
    category: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    created_at: str = None
    relevance_score: float = 0.0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class ProcessingResult:
    """Result of document processing operation"""
    success: bool
    document_id: str
    file_name: str
    file_type: str
    total_pages: int
    total_chunks: int
    language_detected: str
    category: str
    processing_time: float
    error_message: Optional[str] = None
    chunks: List[DocumentChunk] = None
    
    def __post_init__(self):
        if self.chunks is None:
            self.chunks = []

class DocumentProcessingService:
    """
    Multi-format document processing service supporting PDF, Markdown, and text files
    """
    
    def __init__(self, data_dir: str = "backend/data"):
        self.data_dir = Path(data_dir)
        self.embeddings_dir = self.data_dir / "embeddings"
        self.processed_dir = self.data_dir / "processed"
        
        # Create directories if they don't exist
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize embedding model
        self.embedding_model = None
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Embedding model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}")
        
        # Load existing document index
        self.document_index = self._load_document_index()
        
        logger.info(f"Document processing service initialized (PDF: {PDF_AVAILABLE}, Markdown: {MARKDOWN_AVAILABLE}, Embeddings: {EMBEDDINGS_AVAILABLE})")
    
    def _load_document_index(self) -> Dict[str, Any]:
        """Load existing document index"""
        index_file = self.processed_dir / "documents_index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load document index: {e}")
        return {"documents": {}, "last_updated": datetime.now().isoformat()}
    
    def _save_document_index(self):
        """Save document index to file"""
        index_file = self.processed_dir / "documents_index.json"
        self.document_index["last_updated"] = datetime.now().isoformat()
        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(self.document_index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save document index: {e}")
    
    async def upload_and_process_file(self, file_content: bytes, filename: str, 
                                    category: str = "general", language: str = "auto") -> ProcessingResult:
        """
        Upload and process a document file (PDF or Markdown)
        """
        start_time = datetime.now()
        
        try:
            # Determine file type
            file_ext = Path(filename).suffix.lower()
            if file_ext == '.pdf':
                if not PDF_AVAILABLE:
                    raise Exception("PDF processing not available - missing dependencies")
                result = await self._process_pdf_file(file_content, filename, category, language)
            elif file_ext in ['.md', '.markdown']:
                if not MARKDOWN_AVAILABLE:
                    raise Exception("Markdown processing not available - missing dependencies")
                result = await self._process_markdown_file(file_content, filename, category, language)
            elif file_ext == '.txt':
                result = await self._process_text_file(file_content, filename, category, language)
            else:
                raise Exception(f"Unsupported file type: {file_ext}")
            
            if result.success:
                # Update document index
                self.document_index["documents"][result.document_id] = {
                    "filename": result.file_name,
                    "file_type": result.file_type,
                    "category": result.category,
                    "language": result.language_detected,
                    "total_chunks": result.total_chunks,
                    "created_at": datetime.now().isoformat()
                }
                self._save_document_index()
                
                logger.info(f"Document processed successfully: {filename} -> {result.total_chunks} chunks")
            
            result.processing_time = (datetime.now() - start_time).total_seconds()
            return result
            
        except Exception as e:
            error_msg = f"Document processing failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return ProcessingResult(
                success=False,
                document_id="",
                file_name=filename,
                file_type=Path(filename).suffix.lower(),
                total_pages=0,
                total_chunks=0,
                language_detected="unknown",
                category=category,
                processing_time=(datetime.now() - start_time).total_seconds(),
                error_message=error_msg
            )
    
    async def _process_pdf_file(self, file_content: bytes, filename: str, 
                              category: str, language: str) -> ProcessingResult:
        """Process PDF file"""
        # Save temporary file
        temp_file = self.processed_dir / f"temp_{hashlib.md5(file_content).hexdigest()}.pdf"
        with open(temp_file, 'wb') as f:
            f.write(file_content)
        
        try:
            # Extract text
            text_content, total_pages = await self._extract_text_from_pdf(temp_file)
            
            # Auto-detect language if needed
            if language == "auto":
                language = await self._detect_language(text_content)
            
            # Create chunks
            chunks = await self._create_text_chunks(text_content, filename, "pdf", category, language)
            
            # Generate embeddings
            if self.embedding_model:
                await self._generate_embeddings(chunks)
            
            # Save chunks
            document_id = await self._save_chunks(chunks)
            
            return ProcessingResult(
                success=True,
                document_id=document_id,
                file_name=filename,
                file_type="pdf",
                total_pages=total_pages,
                total_chunks=len(chunks),
                language_detected=language,
                category=category,
                processing_time=0,
                chunks=chunks
            )
            
        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()
    
    async def _process_markdown_file(self, file_content: bytes, filename: str, 
                                   category: str, language: str) -> ProcessingResult:
        """Process Markdown file"""
        try:
            # Decode content
            text_content = file_content.decode('utf-8')
            
            # Auto-detect language if needed
            if language == "auto":
                language = await self._detect_language(text_content)
            
            # Parse markdown and convert to sections
            sections = await self._parse_markdown_sections(text_content)
            
            # Create chunks from sections
            chunks = []
            for i, section in enumerate(sections):
                chunk_id = f"{hashlib.md5(filename.encode()).hexdigest()}_{i}"
                chunk = DocumentChunk(
                    id=chunk_id,
                    content=section["content"],
                    source_file=filename,
                    source_type="markdown",
                    page_number=None,
                    chunk_index=i,
                    language=language,
                    category=category,
                    metadata={
                        "section_title": section.get("title", ""),
                        "section_level": section.get("level", 1),
                        "word_count": len(section["content"].split())
                    }
                )
                chunks.append(chunk)
            
            # Generate embeddings
            if self.embedding_model:
                await self._generate_embeddings(chunks)
            
            # Save chunks
            document_id = await self._save_chunks(chunks)
            
            return ProcessingResult(
                success=True,
                document_id=document_id,
                file_name=filename,
                file_type="markdown",
                total_pages=1,  # Markdown doesn't have pages
                total_chunks=len(chunks),
                language_detected=language,
                category=category,
                processing_time=0,
                chunks=chunks
            )
            
        except Exception as e:
            raise Exception(f"Markdown processing failed: {str(e)}")
    
    async def _process_text_file(self, file_content: bytes, filename: str, 
                               category: str, language: str) -> ProcessingResult:
        """Process plain text file"""
        try:
            # Decode content
            text_content = file_content.decode('utf-8')
            
            # Auto-detect language if needed
            if language == "auto":
                language = await self._detect_language(text_content)
            
            # Create chunks
            chunks = await self._create_text_chunks(text_content, filename, "text", category, language)
            
            # Generate embeddings
            if self.embedding_model:
                await self._generate_embeddings(chunks)
            
            # Save chunks
            document_id = await self._save_chunks(chunks)
            
            return ProcessingResult(
                success=True,
                document_id=document_id,
                file_name=filename,
                file_type="text",
                total_pages=1,
                total_chunks=len(chunks),
                language_detected=language,
                category=category,
                processing_time=0,
                chunks=chunks
            )
            
        except Exception as e:
            raise Exception(f"Text processing failed: {str(e)}")
    
    async def _parse_markdown_sections(self, content: str) -> List[Dict[str, Any]]:
        """Parse markdown content into logical sections"""
        sections = []
        lines = content.split('\n')
        current_section = {"title": "", "content": "", "level": 1}
        
        for line in lines:
            # Check for headers
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                # Save previous section if it has content
                if current_section["content"].strip():
                    sections.append(current_section.copy())
                
                # Start new section
                level = len(header_match.group(1))
                title = header_match.group(2)
                current_section = {
                    "title": title,
                    "content": line + "\n",
                    "level": level
                }
            else:
                current_section["content"] += line + "\n"
        
        # Add last section
        if current_section["content"].strip():
            sections.append(current_section)
        
        # If no sections found, treat entire content as one section
        if not sections:
            sections.append({
                "title": "Document Content",
                "content": content,
                "level": 1
            })
        
        return sections
    
    async def _extract_text_from_pdf(self, file_path: Path) -> Tuple[str, int]:
        """Extract text from PDF using multiple methods"""
        try:
            # Method 1: PyMuPDF (fitz) - preferred for better text extraction
            doc = fitz.open(file_path)
            total_pages = doc.page_count
            
            page_texts = []
            for page_num in range(total_pages):
                page = doc[page_num]
                page_text = page.get_text()
                if page_text.strip():
                    page_texts.append(f"[Page {page_num + 1}]\n{page_text}\n")
            
            doc.close()
            text_content = "\n".join(page_texts)
            
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed: {e}, trying PyPDF2...")
            
            # Method 2: PyPDF2 fallback
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    total_pages = len(pdf_reader.pages)
                    
                    page_texts = []
                    for page_num, page in enumerate(pdf_reader.pages):
                        try:
                            page_text = page.extract_text()
                            if page_text.strip():
                                page_texts.append(f"[Page {page_num + 1}]\n{page_text}\n")
                        except Exception as page_e:
                            logger.warning(f"Failed to extract text from page {page_num + 1}: {page_e}")
                    
                    text_content = "\n".join(page_texts)
                    
            except Exception as e2:
                logger.error(f"PyPDF2 extraction also failed: {e2}")
                raise Exception("Failed to extract text from PDF using all available methods")
        
        return text_content, total_pages
    
    async def _detect_language(self, text: str) -> str:
        """
        Auto-detect language based on text characteristics
        """
        text_sample = text[:1000].lower()
        
        # Simple heuristics for language detection
        arabic_chars = sum(1 for char in text_sample if '\u0600' <= char <= '\u06FF')
        french_words = ['le', 'la', 'des', 'une', 'avec', 'pour', 'dans', 'sur', 'est', 'sont']
        french_count = sum(1 for word in french_words if word in text_sample)
        
        # Arabic: significant Arabic characters
        if arabic_chars > 10:
            return "ar"
        # French: common French words detected
        elif french_count > 3:
            return "fr"
        # Default to English
        else:
            return "en"
    
    async def _create_text_chunks(self, text: str, filename: str, source_type: str, 
                                category: str, language: str) -> List[DocumentChunk]:
        """Create text chunks with overlap for better context"""
        chunk_size = 1000
        overlap = 200
        chunks = []
        
        # Split text into sentences for better chunking
        sentences = re.split(r'[.!?]+', text)
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                # Create chunk
                chunk_id = f"{hashlib.md5(filename.encode()).hexdigest()}_{chunk_index}"
                chunk = DocumentChunk(
                    id=chunk_id,
                    content=current_chunk.strip(),
                    source_file=filename,
                    source_type=source_type,
                    page_number=None,
                    chunk_index=chunk_index,
                    language=language,
                    category=category,
                    metadata={
                        "word_count": len(current_chunk.split()),
                        "char_count": len(current_chunk)
                    }
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + " " + sentence
                chunk_index += 1
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add final chunk
        if current_chunk.strip():
            chunk_id = f"{hashlib.md5(filename.encode()).hexdigest()}_{chunk_index}"
            chunk = DocumentChunk(
                id=chunk_id,
                content=current_chunk.strip(),
                source_file=filename,
                source_type=source_type,
                page_number=None,
                chunk_index=chunk_index,
                language=language,
                category=category,
                metadata={
                    "word_count": len(current_chunk.split()),
                    "char_count": len(current_chunk)
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _generate_embeddings(self, chunks: List[DocumentChunk]):
        """Generate embeddings for document chunks"""
        if not self.embedding_model:
            logger.warning("Embedding model not available, skipping embedding generation")
            return
        
        try:
            texts = [chunk.content for chunk in chunks]
            embeddings = self.embedding_model.encode(texts, batch_size=32, show_progress_bar=False)
            
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding.tolist()
                
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
    
    async def _save_chunks(self, chunks: List[DocumentChunk]) -> str:
        """Save document chunks to storage"""
        if not chunks:
            return ""
        
        document_id = chunks[0].id.split('_')[0]
        
        # Save chunks as JSON
        chunks_file = self.embeddings_dir / f"{document_id}_chunks.json"
        chunks_data = [asdict(chunk) for chunk in chunks]
        
        try:
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump(chunks_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(chunks)} chunks to {chunks_file}")
            return document_id
            
        except Exception as e:
            logger.error(f"Failed to save chunks: {e}")
            return ""
    
    async def search_documents(self, query: str, language: str = None, 
                             category: str = None, max_results: int = 5) -> List[DocumentChunk]:
        """Search documents using embeddings and keyword matching"""
        all_chunks = []
        
        # Load all chunk files
        for chunk_file in self.embeddings_dir.glob("*_chunks.json"):
            try:
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    chunks_data = json.load(f)
                    for chunk_data in chunks_data:
                        chunk = DocumentChunk(**chunk_data)
                        all_chunks.append(chunk)
            except Exception as e:
                logger.error(f"Failed to load chunks from {chunk_file}: {e}")
        
        if not all_chunks:
            return []
        
        # Filter by language and category
        filtered_chunks = []
        for chunk in all_chunks:
            if language and chunk.language != language:
                continue
            if category and chunk.category != category:
                continue
            filtered_chunks.append(chunk)
        
        if not filtered_chunks:
            return []
        
        # Embedding-based search
        if self.embedding_model and any(chunk.embedding for chunk in filtered_chunks):
            query_embedding = self.embedding_model.encode([query])[0]
            
            for chunk in filtered_chunks:
                if chunk.embedding:
                    # Calculate cosine similarity
                    chunk_embedding = np.array(chunk.embedding)
                    similarity = np.dot(query_embedding, chunk_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
                    )
                    chunk.relevance_score = float(similarity)
                else:
                    chunk.relevance_score = 0.0
        else:
            # Keyword-based fallback search
            query_lower = query.lower()
            for chunk in filtered_chunks:
                content_lower = chunk.content.lower()
                # Simple keyword matching score
                query_words = query_lower.split()
                matches = sum(1 for word in query_words if word in content_lower)
                chunk.relevance_score = matches / len(query_words) if query_words else 0.0
        
        # Sort by relevance and return top results
        sorted_chunks = sorted(filtered_chunks, key=lambda x: x.relevance_score, reverse=True)
        return sorted_chunks[:max_results]
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get comprehensive document processing statistics"""
        stats = {
            "total_documents": len(self.document_index["documents"]),
            "total_chunks": 0,
            "categories": {},
            "languages": {},
            "file_types": {},
            "storage_mb": 0.0
        }
        
        # Calculate statistics
        for doc_id, doc_info in self.document_index["documents"].items():
            stats["total_chunks"] += doc_info.get("total_chunks", 0)
            
            category = doc_info.get("category", "unknown")
            stats["categories"][category] = stats["categories"].get(category, 0) + 1
            
            language = doc_info.get("language", "unknown")
            stats["languages"][language] = stats["languages"].get(language, 0) + 1
            
            file_type = doc_info.get("file_type", "unknown")
            stats["file_types"][file_type] = stats["file_types"].get(file_type, 0) + 1
        
        # Calculate storage usage
        try:
            for file_path in self.embeddings_dir.glob("*.json"):
                stats["storage_mb"] += file_path.stat().st_size / (1024 * 1024)
        except Exception as e:
            logger.warning(f"Failed to calculate storage usage: {e}")
        
        return stats

# Global service instance
document_processing_service = DocumentProcessingService()

# Convenience functions for backward compatibility
async def process_pdf_file(file_content: bytes, filename: str, category: str = "general", language: str = "auto"):
    return await document_processing_service.upload_and_process_file(file_content, filename, category, language)

async def search_pdf_documents(query: str, language: str = None, category: str = None, max_results: int = 5):
    return await document_processing_service.search_documents(query, language, category, max_results) 