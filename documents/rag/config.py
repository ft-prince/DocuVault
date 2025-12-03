"""
Configuration settings for RAG module
"""

import os
from pathlib import Path


class RAGConfig:
    """Configuration class for RAG system"""
    
    # Model configurations
    #EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-0.6B"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    LLM_MODEL = "llama-3.1-8b-instant"
    #Qwen/Qwen2.5-7B - replacing this with a smaller model may help with resource constraints

    # Text chunking parameters
    CHUNK_SIZE = 256
    CHUNK_OVERLAP = 60
    
    # Retrieval parameters
    N_RESULTS = 6  # Number of chunks to retrieve
    SIMILARITY_THRESHOLD = 0.05  # Minimum similarity score
    
    # LLM generation parameters
    MAX_NEW_TOKENS = 512
    TEMPERATURE = 0.2
    TOP_P = 0.85
    REPETITION_PENALTY = 1.1
    
    # Question rewriting parameters
    REWRITE_MAX_TOKENS = 30
    REWRITE_TEMPERATURE = 0.1
    REWRITE_MAX_HISTORY = 4  # Number of previous turns to consider
    
    # Conversation memory settings
    MAX_MEMORY_TOKEN_LIMIT = 2000
    MAX_HISTORY_TURNS = 6  # Maximum conversation history to include in context
    
    # Vector store configuration
    CHROMA_DB_PATH = None  # Will be set dynamically
    COLLECTION_NAME = "docuvault_documents"
    
    # Device configuration
    DEVICE = None  # Will be auto-detected (cuda/cpu)
    
    # Embedding batch size
    EMBEDDING_BATCH_SIZE = 16
    
    # 8-bit quantization config for LLM
    USE_8BIT_QUANTIZATION = True
    LLM_INT8_THRESHOLD = 6.0
    
    # Text splitting separators
    TEXT_SEPARATORS = ["\n\n", "\n", " ", ""]
    
    # System prompt for RAG
    SYSTEM_PROMPT = """You are a helpful AI assistant specialized in answering questions based strictly on provided context.

STRICT RULES:
1. Answer ONLY using information explicitly stated in the Context section
2. If the context doesn't contain the answer, respond with: "I cannot find this information in the provided documents."
3. DO NOT use your general knowledge or training data
4. DO NOT make up information, names, dates, or facts
5. When referencing information, cite the source document

If the question is outside the scope of the provided documents, politely decline to answer."""
    
    # Rewrite system prompt
    REWRITE_SYSTEM_PROMPT = "Rewrite the follow-up question to be standalone. Output ONLY the rewritten question - no explanations."
    
    # Stop token IDs for generation
    STOP_TOKEN_IDS = [151645]  # Additional stop tokens for Qwen
    
    @classmethod
    def set_chroma_path(cls, base_path):
        """Set ChromaDB storage path"""
        cls.CHROMA_DB_PATH = os.path.join(base_path, 'chroma_db')
        os.makedirs(cls.CHROMA_DB_PATH, exist_ok=True)
    
    @classmethod
    def set_device(cls, device):
        """Set computation device"""
        cls.DEVICE = device
