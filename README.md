# 🤖 Simple RAG Chatbot

A clean, minimal **Retrieval Augmented Generation (RAG)** chatbot with document upload capabilities and automatic language detection.

## ✨ Features

- **💬 Intelligent Chat**: Context-aware responses using uploaded documents
- **📤 Multi-format Upload**: Support for PDF, Markdown, Text, and JSON files
- **🌍 Auto Language Detection**: Automatically detects and responds in EN/AR/FR
- **🔍 Document Search**: Semantic search across all uploaded documents
- **🚀 Simple API**: Clean, minimal endpoints for easy integration

## 🏗️ Architecture

```
Simple RAG System:
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Documents     │    │   RAG Chatbot    │    │   Chat API      │
│ (PDF/MD/TXT/JSON)│ →  │   + Embeddings   │ →  │  + Language     │
│                 │    │   + Retrieval    │    │    Detection    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🔄 **Complete RAG Flow**

```
📤 Upload Document
        ↓
🔀 Text Chunking (1000 chars + 200 overlap)
        ↓
🧠 Generate Embeddings (384-dim vectors)
        ↓
💾 Save Chunks + Embeddings (JSON files)
        ↓
📝 Update Document Index
        ↓
✅ Ready for RAG Chat!

💬 User Query
        ↓
🌍 Detect Language (EN/AR/FR)
        ↓
🔍 Search Embeddings (cosine similarity)
        ↓
📊 Rank by Relevance Score
        ↓
🎯 Get Top 3 Relevant Chunks
        ↓
🤖 Generate Context-Aware Response
        ↓
📤 Return Response + Sources
```

## 💾 **Data Storage: File-Based (No Database!)**

The RAG system uses **simple file storage** instead of a complex database:

```
backend/data/
├── documents/          # 📋 Initial JSON data files
│   ├── services.json
│   ├── training.json
│   └── faq.json
├── uploads/           # 📤 Raw uploaded files (temporary)
├── processed/         # 📊 Document metadata & index
│   └── documents_index.json
└── embeddings/        # 🧠 Processed chunks + embeddings
    ├── doc_abc123_chunks.json
    ├── doc_def456_chunks.json
    └── ...
```

### **What Gets Created After Upload:**

**📊 Document Index** (`documents_index.json`):
```json
{
  "documents": {
    "doc_abc123": {
      "filename": "my_document.pdf",
      "file_type": "pdf",
      "language": "en",
      "total_chunks": 8,
      "created_at": "2024-06-30T10:30:00Z"
    }
  }
}
```

**🧠 Document Chunks** (`doc_abc123_chunks.json`):
```json
[
  {
    "id": "doc_abc123_0",
    "content": "Our company provides comprehensive cloud services...",
    "embedding": [0.123, -0.456, 0.789, ...], // 384 numbers
    "source_file": "my_document.pdf",
    "language": "en",
    "relevance_score": 0.0
  }
]
```

### **Advantages:**
- **🚀 Zero Setup**: No database installation required
- **📱 Portable**: Copy `backend/data/` folder anywhere  
- **🔍 Easy Debug**: Open JSON files to see exactly what's stored
- **💾 Simple Backup**: Just copy the directory
- **🎓 Perfect for Learning**: Understand exactly how RAG works

## 📡 API Endpoints

### Core APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/chat` | 💬 Chat with RAG context |
| `POST` | `/api/v1/upload` | 📤 Upload documents |
| `GET` | `/api/v1/documents` | 📋 List uploaded documents |
| `DELETE` | `/api/v1/documents/{id}` | 🗑️ Delete document |
| `GET` | `/api/v1/health` | 💓 Health check |

### Chat API

**POST** `/api/v1/chat`

```json
{
  "message": "What services do you offer?",
  "include_context": true,
  "max_context": 3
}
```

**Response:**
```json
{
  "response": "Based on the available documents, I can help with...",
  "language": "en",
  "sources": [
    {
      "filename": "services.json",
      "type": "json",
      "relevance": 0.85,
      "content_preview": "Digital transformation services..."
    }
  ],
  "context_used": true,
  "confidence": 0.85
}
```

### Upload API

**POST** `/api/v1/upload`

```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@document.pdf" \
  -F "category=general"
```

**Response:**
```json
{
  "success": true,
  "document_id": "doc_123",
  "filename": "document.pdf",
  "file_type": "pdf",
  "chunks": 12,
  "language": "en"
}
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd LLM-based-assistant

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

Create `.env` file:
```bash
# Optional: OpenAI API key for enhanced responses
OPENAI_API_KEY=your_openai_key_here

# File upload settings
UPLOAD_DIR=backend/data/uploads
EMBEDDINGS_DIR=backend/data/embeddings
MAX_FILE_SIZE=10485760  # 10MB

# Server settings
PORT=8000
DEBUG=false
```

### 3. Run the Server

```bash
# Main server
cd backend
python -m app.main

# Or demo server
python working_demo_server.py
```

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Chat
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how can you help me?"}'

# Upload document
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@sample.pdf"
```

## 📁 Supported File Types

- **PDF** (`.pdf`) - Text extraction with OCR fallback
- **Markdown** (`.md`, `.markdown`) - Section-based parsing
- **Text** (`.txt`) - Plain text chunking
- **JSON** (`.json`) - Structured data processing

## 🌍 Language Support

- **English** (`en`) - Default language
- **Arabic** (`ar`) - RTL support with Arabic script detection
- **French** (`fr`) - European language support

## 🏃‍♂️ Testing with Demo Server

```bash
# Start demo server
python working_demo_server.py

# Open browser
http://localhost:8001/docs
```

The demo server provides mock responses for testing without setting up the full backend.

## 📚 API Documentation

- **Interactive Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## 🔧 Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Server port |
| `DEBUG` | `false` | Debug mode |
| `UPLOAD_DIR` | `backend/data/uploads` | File upload directory |
| `EMBEDDINGS_DIR` | `backend/data/embeddings` | Embeddings storage |
| `MAX_FILE_SIZE` | `10MB` | Maximum file size |
| `OPENAI_API_KEY` | - | OpenAI API key (optional) |

## 📝 Example Usage

### Python Client

```python
import requests

# Chat
response = requests.post("http://localhost:8000/api/v1/chat", json={
    "message": "What training programs do you offer?",
    "include_context": True
})
print(response.json())

# Upload
with open("document.pdf", "rb") as f:
    response = requests.post("http://localhost:8000/api/v1/upload", 
                           files={"file": f})
print(response.json())
```

### JavaScript Client

```javascript
// Chat
const chatResponse = await fetch('/api/v1/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        message: "Hello, how can you help?",
        include_context: true
    })
});

// Upload
const formData = new FormData();
formData.append('file', fileInput.files[0]);
const uploadResponse = await fetch('/api/v1/upload', {
    method: 'POST',
    body: formData
});
```

## 🎯 Perfect for University Projects

This system is designed to be:
- **Simple** - Clean architecture without over-engineering
- **Educational** - Easy to understand and extend
- **Functional** - Working RAG implementation
- **Documented** - Comprehensive API documentation
- **Multilingual** - Real-world language support

## 🚀 Deployment

### Docker (Recommended)

```bash
docker-compose up --build
```

### Manual Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Run with production server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

---

**🎓 Built for simplicity and education - perfect for university AI projects!** 