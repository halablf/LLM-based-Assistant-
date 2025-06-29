"""
Simple logging configuration for RAG Chatbot
"""

import logging
import sys
from typing import Any, Dict
import json
from datetime import datetime
import os

# Simple config - no complex settings object
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
            
        if hasattr(record, 'method'):
            log_entry["method"] = record.method
            
        if hasattr(record, 'url'):
            log_entry["url"] = record.url
            
        if hasattr(record, 'status_code'):
            log_entry["status_code"] = record.status_code
            
        if hasattr(record, 'duration_seconds'):
            log_entry["duration_seconds"] = record.duration_seconds
        
        # Add exception info
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add any extra fields
        extra_fields = getattr(record, 'extra', {})
        if extra_fields:
            log_entry.update(extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging():
    """Configure application logging."""
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Configure structured logging for production
    if not DEBUG:
        # Remove default handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add JSON formatter
        json_handler = logging.StreamHandler(sys.stdout)
        json_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(json_handler)
    
    # Set levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    # Application logger
    app_logger = logging.getLogger("app")
    app_logger.info(f"🚀 RAG Chatbot logging configured - Level: {LOG_LEVEL}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(f"app.{name}")


# Create default logger for immediate use
logger = logging.getLogger("app.rag_chatbot")


class LoggerMixin:
    """Mixin class to add logging to any class."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return get_logger(self.__class__.__name__) 