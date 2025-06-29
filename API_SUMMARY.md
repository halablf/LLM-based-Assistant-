# 🚀 RAG Chatbot - Concise API List

## ✅ **ESSENTIAL APIs ONLY** (4 Core Endpoints)

### 1. 💬 **Chat** - `/api/v1/chat` (POST)
**Purpose**: Main RAG chat with document context
```json
{
  "message": "What services do you offer?",
  "include_context": true,
  "max_context": 3
}
```

### 2. 📤 **Upload** - `/api/v1/upload` (POST)
**Purpose**: Upload documents (PDF/MD/TXT/JSON)
```bash
curl -X POST /api/v1/upload -F "file=@document.pdf"
```

### 3. 📋 **List Documents** - `/api/v1/documents` (GET)
**Purpose**: List all uploaded documents
```json
[
  {
    "id": "doc_123",
    "filename": "services.pdf",
    "file_type": "pdf",
    "language": "en",
    "chunks": 12
  }
]
```

### 4. 💓 **Health Check** - `/api/v1/health` (GET)
**Purpose**: System status check
```json
{
  "status": "healthy",
  "service": "RAG Chatbot",
  "version": "1.0.0"
}
```

---

## 🏗️ **Simple Architecture**

```
User → Upload Docs → RAG System → Chat with Context
```

## ✨ **Key Features**
- **Auto Language Detection** (EN/AR/FR)
- **Multi-format Upload** (PDF, Markdown, Text, JSON)
- **RAG Context** from uploaded documents
- **No complex routing** - Direct chat interface
- **Swagger docs** at `/docs`

## 🚀 **Quick Test**
```bash
# 1. Health
curl http://localhost:8000/api/v1/health

# 2. Chat
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'

# 3. Upload
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@test.pdf"
```

**That's it! Clean, simple, working RAG chatbot.** 🎯 