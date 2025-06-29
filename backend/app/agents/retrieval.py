"""
Enhanced Document Retrieval Agent - RAG-based document search and retrieval
Supports both JSON data and PDF documents with embedding-based similarity search
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import hashlib
from ..services.llm_service import LLMService
from ..services.data_service import DataService
from ..services.pdf_processing_service import pdf_processing_service, DocumentChunk

@dataclass
class DocumentChunk:
    id: str
    content: str
    source: str
    category: str
    language: str
    metadata: Dict[str, Any]
    relevance_score: float = 0.0

class DocumentRetrievalAgent:
    """
    Specialized agent for document retrieval and RAG-based responses
    """
    
    def __init__(self):
        self.llm_service = LLMService()
        self.data_service = DataService()
        
    async def retrieve_relevant_documents(
        self, 
        query: str, 
        language: str = "en",
        max_results: int = 5,
        include_pdfs: bool = True,
        category_filter: Optional[str] = None
    ) -> List[DocumentChunk]:
        """
        Enhanced retrieval: Combines JSON data and PDF documents using embedding similarity
        """
        all_docs = []
        
        # Get JSON-based documents (existing functionality)
        json_docs = await self._get_all_documents()
        all_docs.extend(json_docs)
        
        # Get PDF-based documents (new functionality)
        if include_pdfs:
            try:
                pdf_docs = await pdf_processing_service.search_documents(
                    query=query,
                    language=language if language != "auto" else None,
                    category=category_filter,
                    max_results=max_results * 2,  # Get more PDF results for better mixing
                    similarity_threshold=0.2
                )
                
                # Convert PDF DocumentChunks to our format for compatibility
                for pdf_doc in pdf_docs:
                    json_doc = DocumentChunk(
                        id=pdf_doc.id,
                        content=pdf_doc.content,
                        source=pdf_doc.source_file,
                        category=f"pdf_{pdf_doc.category}",
                        language=pdf_doc.language,
                        metadata={
                            **pdf_doc.metadata,
                            "source_type": "pdf",
                            "page_number": pdf_doc.page_number,
                            "chunk_index": pdf_doc.chunk_index,
                            "embedding_score": pdf_doc.relevance_score
                        },
                        relevance_score=pdf_doc.relevance_score
                    )
                    all_docs.append(json_doc)
                    
            except Exception as e:
                # PDF search failed, continue with JSON only
                pass
        
        # For JSON documents, calculate relevance if not already done
        for doc in all_docs:
            if not hasattr(doc, 'relevance_score') or doc.relevance_score == 0.0:
                doc.relevance_score = await self._calculate_relevance(query, doc, language)
        
        # Filter by relevance threshold and category
        filtered_docs = []
        for doc in all_docs:
            if doc.relevance_score > 0.2:  # Lower threshold for mixed results
                if category_filter:
                    if category_filter in doc.category or doc.category.endswith(category_filter):
                        filtered_docs.append(doc)
                else:
                    filtered_docs.append(doc)
        
        # Sort by relevance and return top results
        filtered_docs.sort(key=lambda x: x.relevance_score, reverse=True)
        return filtered_docs[:max_results]
    
    async def generate_rag_response(
        self, 
        query: str, 
        retrieved_docs: List[DocumentChunk], 
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Generate response using retrieved documents as context
        """
        # Prepare context from retrieved documents
        context_chunks = []
        for doc in retrieved_docs:
            context_chunks.append(f"""
            Source: {doc.source} ({doc.category})
            Content: {doc.content[:500]}...
            """)
        
        context = "\n---\n".join(context_chunks)
        
        system_prompt = f"""
        You are Expert Company's AI assistant. Use the provided context to answer user queries accurately.
        Always cite sources when providing information and indicate if information is not available in the context.
        
        Available Context:
        {context}
        
        Response Guidelines:
        - Use only information from the provided context
        - Cite sources when making claims
        - Indicate if the query cannot be fully answered with available information
        - Respond in {language} language
        - Maintain professional tone appropriate for petroleum/training industry
        """
        
        user_prompt = f"""
        User query: "{query}"
        
        Provide a comprehensive response based on the available context.
        """
        
        try:
            response = await self.llm_service.generate_response(
                message=user_prompt,
                system_prompt=system_prompt,
                temperature=0.2
            )
            
            return {
                "response": response,
                "sources": [{"source": doc.source, "category": doc.category} for doc in retrieved_docs],
                "confidence": self._calculate_response_confidence(retrieved_docs),
                "language": language
            }
        except Exception as e:
            return {
                "response": "I apologize, but I'm unable to process your query at the moment. Please try again or contact our support team.",
                "sources": [],
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def _get_all_documents(self) -> List[DocumentChunk]:
        """
        Get all available documents as chunks
        """
        documents = []
        
        # Load petroleum services data
        petroleum_data = await self.data_service.get_petroleum_services()
        documents.extend(self._create_chunks_from_data(petroleum_data, "petroleum_services"))
        
        # Load training services data
        training_data = await self.data_service.get_training_services()
        documents.extend(self._create_chunks_from_data(training_data, "training_services"))
        
        # Load FAQ data
        faq_data = await self.data_service.get_faq_data()
        documents.extend(self._create_chunks_from_data(faq_data, "faq"))
        
        # Load multilingual data
        for lang in ["ar", "fr"]:
            try:
                multilingual_data = await self.data_service.get_services_data(lang)
                documents.extend(self._create_chunks_from_data(multilingual_data, f"services_{lang}"))
            except:
                continue
        
        return documents
    
    def _create_chunks_from_data(self, data: Dict, category: str) -> List[DocumentChunk]:
        """
        Create document chunks from structured data
        """
        chunks = []
        language = data.get("language", "en")
        
        if "content" in data:
            for key, value in data["content"].items():
                chunk_id = hashlib.md5(f"{category}_{key}".encode()).hexdigest()[:8]
                
                # Create chunk content
                content_parts = []
                if isinstance(value, dict):
                    if "description" in value:
                        content_parts.append(f"Description: {value['description']}")
                    
                    for subkey, subvalue in value.items():
                        if subkey != "description" and isinstance(subvalue, (list, str)):
                            if isinstance(subvalue, list):
                                content_parts.append(f"{subkey.replace('_', ' ').title()}: {', '.join(subvalue)}")
                            else:
                                content_parts.append(f"{subkey.replace('_', ' ').title()}: {subvalue}")
                
                content = "\n".join(content_parts)
                
                chunk = DocumentChunk(
                    id=chunk_id,
                    content=content,
                    source=data.get("title", category),
                    category=category,
                    language=language,
                    metadata={
                        "section": key,
                        "created_at": data.get("created_at", ""),
                        "version": data.get("version", "1.0")
                    }
                )
                chunks.append(chunk)
        
        return chunks
    
    async def _calculate_relevance(self, query: str, document: DocumentChunk, language: str) -> float:
        """
        Calculate relevance score between query and document
        """
        query_lower = query.lower()
        content_lower = document.content.lower()
        
        # Simple keyword matching (in production, would use embeddings)
        query_words = set(query_lower.split())
        content_words = set(content_lower.split())
        
        # Calculate Jaccard similarity
        intersection = query_words.intersection(content_words)
        union = query_words.union(content_words)
        
        jaccard_score = len(intersection) / len(union) if union else 0
        
        # Boost score for language match
        language_boost = 1.2 if document.language == language else 1.0
        
        # Boost score for category relevance
        category_boost = 1.0
        if any(keyword in query_lower for keyword in ["drilling", "petroleum", "oil", "gas"]):
            if document.category == "petroleum_services":
                category_boost = 1.3
        elif any(keyword in query_lower for keyword in ["training", "course", "certification"]):
            if document.category == "training_services":
                category_boost = 1.3
        
        return jaccard_score * language_boost * category_boost
    
    def _calculate_response_confidence(self, retrieved_docs: List[DocumentChunk]) -> float:
        """
        Calculate confidence in the response based on retrieved documents
        """
        if not retrieved_docs:
            return 0.0
        
        # Average relevance score
        avg_relevance = sum(doc.relevance_score for doc in retrieved_docs) / len(retrieved_docs)
        
        # Number of sources factor
        source_factor = min(1.0, len(retrieved_docs) / 3)  # Optimal around 3 sources
        
        return min(0.95, avg_relevance * source_factor)
    
    async def search_documents(
        self, 
        query: str, 
        category: Optional[str] = None,
        language: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        Search documents and return structured results
        """
        retrieved_docs = await self.retrieve_relevant_documents(query, language)
        
        # Filter by category if specified
        if category:
            retrieved_docs = [doc for doc in retrieved_docs if doc.category == category]
        
        return [
            {
                "id": doc.id,
                "title": doc.metadata.get("section", "").replace('_', ' ').title(),
                "content_preview": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                "source": doc.source,
                "category": doc.category,
                "language": doc.language,
                "relevance_score": doc.relevance_score
            }
            for doc in retrieved_docs
        ] 