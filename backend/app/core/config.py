"""
Simple configuration for RAG Chatbot
"""

import os
from typing import List

# Basic App Config
APP_NAME = "RAG Chatbot"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# API Configuration
API_V1_PREFIX = "/api/v1"
PORT = int(os.getenv("PORT", 8000))

# OpenAI Configuration (if needed)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# File Upload Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "backend/data/uploads")
EMBEDDINGS_DIR = os.getenv("EMBEDDINGS_DIR", "backend/data/embeddings")

# Language Configuration
SUPPORTED_LANGUAGES = ["en", "ar", "fr"]
DEFAULT_LANGUAGE = "en"

# Document Processing
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_CHUNKS_PER_DOCUMENT = 100

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EMBEDDINGS_DIR, exist_ok=True) 