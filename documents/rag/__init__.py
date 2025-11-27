"""
RAG (Retrieval-Augmented Generation) Module for DocuVault DMS

This module provides intelligent document querying capabilities using:
- Document processing and chunking
- Embedding generation
- Vector storage and retrieval
- LLM-based question answering
"""

from .config import RAGConfig
from .conversation import RAGChatbot

__all__ = ['RAGConfig', 'RAGChatbot']
