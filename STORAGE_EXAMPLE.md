# 📁 RAG Storage System - File-Based (No Database)

## 🚀 **What Happens When You Upload**

### Step 1: File Upload
```bash
curl -X POST /api/v1/upload -F "file=@my_document.pdf"
```

### Step 2: Document Processing
The system creates these files:

## 📊 **1. Document Index** (`backend/data/processed/documents_index.json`)
```json
{
  "documents": {
    "doc_abc123": {
      "filename": "my_document.pdf",
      "file_type": "pdf", 
      "category": "general",
      "language": "en",
      "total_chunks": 8,
      "created_at": "2024-06-30T10:30:00Z"
    },
    "doc_def456": {
      "filename": "services.md",
      "file_type": "md",
      "category": "services", 
      "language": "en",
      "total_chunks": 12,
      "created_at": "2024-06-30T11:15:00Z"
    }
  },
  "last_updated": "2024-06-30T11:15:00Z"
}
```

## 🧠 **2. Document Chunks** (`backend/data/embeddings/doc_abc123_chunks.json`)
```json
[
  {
    "id": "doc_abc123_0",
    "content": "Our company provides comprehensive cloud services including AWS migration, Azure deployment, and Google Cloud integration. We have over 10 years of experience...",
    "source_file": "my_document.pdf",
    "source_type": "pdf",
    "page_number": 1,
    "chunk_index": 0,
    "language": "en",
    "category": "general",
    "metadata": {
      "word_count": 185,
      "char_count": 987
    },
    "embedding": [0.123, -0.456, 0.789, 0.234, -0.567, ...], // 384 numbers
    "created_at": "2024-06-30T10:30:00Z",
    "relevance_score": 0.0
  },
  {
    "id": "doc_abc123_1", 
    "content": "We also offer training programs in cloud technologies. Our certified instructors provide hands-on experience with real-world projects...",
    "source_file": "my_document.pdf",
    "source_type": "pdf",
    "page_number": 1,
    "chunk_index": 1,
    "language": "en",
    "category": "general",
    "metadata": {
      "word_count": 156,
      "char_count": 823
    },
    "embedding": [0.345, -0.678, 0.912, 0.123, -0.234, ...], // 384 numbers
    "created_at": "2024-06-30T10:30:00Z",
    "relevance_score": 0.0
  }
]
```

---

## 🔍 **How Search Works (No Database Queries)**

When you chat: `"What cloud services do you offer?"`

### Step 1: Load All Chunk Files
```python
# The system reads ALL chunk files
for chunk_file in embeddings_dir.glob("*_chunks.json"):
    with open(chunk_file, 'r') as f:
        chunks = json.load(f)
        all_chunks.extend(chunks)
```

### Step 2: Calculate Similarity
```python
# Convert your question to embedding
query_embedding = model.encode(["What cloud services do you offer?"])

# Compare with each chunk's embedding
for chunk in all_chunks:
    similarity = cosine_similarity(query_embedding, chunk['embedding'])
    chunk['relevance_score'] = similarity
```

### Step 3: Return Best Matches
```python
# Sort by similarity and return top 3
best_chunks = sorted(all_chunks, key=lambda x: x['relevance_score'], reverse=True)[:3]
```

---

## 💡 **Key Points**

✅ **No Database**: Everything stored in JSON files  
✅ **No SQL**: Pure file system operations  
✅ **No Server Setup**: Just directories and files  
✅ **Portable**: Copy the `backend/data/` folder anywhere  
✅ **Simple**: Easy to backup, debug, and understand  

## 📈 **Performance**

- **Small scale** (< 1000 docs): Very fast
- **Medium scale** (1000-10000 docs): Still good  
- **Large scale** (> 10000 docs): Consider database migration

## 🎯 **Perfect for University Projects**

This file-based approach is ideal because:
- No database setup required
- Easy to understand and debug  
- Zero configuration
- Works everywhere
- Perfect for learning RAG concepts

---

## 🚀 **Want to See It in Action?**

```bash
# 1. Upload a document
curl -X POST http://localhost:8000/api/v1/upload -F "file=@test.pdf"

# 2. Check the created files
ls -la backend/data/embeddings/
ls -la backend/data/processed/

# 3. Chat and see it use the uploaded content
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What does the document say about services?"}'
```

**That's it! Simple file-based RAG with no database complexity.** 🎯 