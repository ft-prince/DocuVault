"""
Enhanced Configuration Settings for Multi-Modal RAG System
"""

import os
from pathlib import Path


class RAGConfig:
    """Enhanced configuration class for multi-modal RAG system"""
    
    # ==================== Model Configurations ====================
    
    # Embedding model (all-MiniLM-L6-v2 is fast and efficient)
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    # Alternatives:
    # - "sentence-transformers/all-mpnet-base-v2" (better quality, slower)
    # - "BAAI/bge-small-en-v1.5" (good balance)
    
    # LLM model
    LLM_MODEL = "llama-3.1-8b-instant"  # Groq API
    # Alternatives for local:
    # - "Qwen/Qwen2.5-7B-Instruct"
    # - "meta-llama/Llama-3.2-3B-Instruct"
    
    # Image understanding model
    IMAGE_MODEL = "Salesforce/blip2-opt-2.7b"
    # Alternatives:
    # - "Salesforce/blip2-flan-t5-xl" (better but larger)
    
    # ==================== Text Processing ====================
    
    # Chunking parameters
    CHUNK_SIZE = 512  # Increased for better context
    CHUNK_OVERLAP = 100
    
    # Text separators (hierarchical splitting)
    TEXT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]
    
    # ==================== Retrieval Settings ====================
    
    # Number of chunks to retrieve
    N_RESULTS = 8  # Increased for better coverage
    
    # Minimum similarity threshold
    SIMILARITY_THRESHOLD = 0.05  # Low threshold, let hybrid search handle it
    
    # Hybrid search weights
    SEMANTIC_WEIGHT = 0.7  # 70% semantic, 30% keyword
    USE_HYBRID_SEARCH = True
    
    # Re-ranking parameters
    ENABLE_RERANKING = True
    
    # ==================== LLM Generation ====================
    
    # Generation parameters
    MAX_NEW_TOKENS = 512
    TEMPERATURE = 0.2
    TOP_P = 0.85
    REPETITION_PENALTY = 1.1
    
    # Question rewriting
    REWRITE_MAX_TOKENS = 50
    REWRITE_TEMPERATURE = 0.1
    REWRITE_MAX_HISTORY = 4
    
    # ==================== Memory & Context ====================
    
    # Conversation memory
    MAX_MEMORY_TOKEN_LIMIT = 3000  # Increased for longer conversations
    MAX_HISTORY_TURNS = 8
    
    # Context window for LLM
    MAX_CONTEXT_LENGTH = 4000
    
    # ==================== Multi-Modal Processing ====================
    
    # Table extraction
    ENABLE_TABLE_EXTRACTION = True
    TABLE_EXTRACTION_METHOD = "pdfplumber"  # or "camelot"
    
    # OCR settings
    ENABLE_OCR = True
    OCR_DPI = 300
    OCR_LANG = "eng"
    
    # Image understanding
    ENABLE_IMAGE_DESCRIPTION = False  # Disable by default (resource intensive)
    IMAGE_DESCRIPTION_MAX_TOKENS = 100
    
    # ==================== Vector Store ====================
    
    CHROMA_DB_PATH = None  # Set dynamically
    COLLECTION_NAME = "docuvault_documents_enhanced"
    
    # ==================== Performance ====================
    
    DEVICE = None  # Auto-detected
    EMBEDDING_BATCH_SIZE = 32  # Increased for better throughput
    
    # Quantization for LLM (if using local models)
    USE_8BIT_QUANTIZATION = True
    LLM_INT8_THRESHOLD = 6.0
    
    # ==================== System Prompts ====================
    
    SYSTEM_PROMPT = """You are an advanced AI assistant specialized in answering questions based on document content.

CAPABILITIES:
- You can understand text, tables, and image descriptions from documents
- You provide accurate answers with proper citations
- You distinguish between different types of content (text, tables, images)

STRICT RULES:
1. Answer ONLY using information from the Context section below
2. When referencing tables, mention "according to the table on page X"
3. When referencing images, mention "based on the image description from page X"
4. If information is not in the context, say: "I cannot find this information in the provided documents."
5. NEVER use general knowledge or make assumptions beyond the provided context
6. Always cite sources with [Source X, Page Y] format
7. If you see conflicting information, mention both sources

RESPONSE FORMAT:
- Give direct, clear answers
- Use bullet points for lists or multiple items from tables
- Quote specific numbers or data points from tables when relevant
- Mention if information comes from a visual element (table/image)

Remember: Accuracy and source attribution are more important than completeness."""

    REWRITE_SYSTEM_PROMPT = """Rewrite the follow-up question as a standalone question that includes necessary context from the conversation history.

Rules:
- Keep the rewritten question concise (1-2 sentences max)
- Include only essential context
- Maintain the original intent
- Output ONLY the rewritten question - no explanations
- If the question is already standalone, output it unchanged"""
    
    # Stop tokens
    STOP_TOKEN_IDS = [151645]
    
    # ==================== Methods ====================
    
    @classmethod
    def set_chroma_path(cls, base_path: str):
        """Set ChromaDB storage path"""
        cls.CHROMA_DB_PATH = os.path.join(base_path, 'chroma_db_enhanced')
        os.makedirs(cls.CHROMA_DB_PATH, exist_ok=True)
    
    @classmethod
    def set_device(cls, device: str):
        """Set computation device"""
        cls.DEVICE = device
    
    @classmethod
    def get_config_summary(cls) -> dict:
        """Get summary of current configuration"""
        return {
            'embedding_model': cls.EMBEDDING_MODEL,
            'llm_model': cls.LLM_MODEL,
            'chunk_size': cls.CHUNK_SIZE,
            'n_results': cls.N_RESULTS,
            'hybrid_search': cls.USE_HYBRID_SEARCH,
            'table_extraction': cls.ENABLE_TABLE_EXTRACTION,
            'ocr_enabled': cls.ENABLE_OCR,
            'image_description': cls.ENABLE_IMAGE_DESCRIPTION,
            'device': cls.DEVICE or 'auto'
        }
    
    @classmethod
    def enable_all_features(cls):
        """Enable all multi-modal features (requires more resources)"""
        cls.ENABLE_TABLE_EXTRACTION = True
        cls.ENABLE_OCR = True
        cls.ENABLE_IMAGE_DESCRIPTION = True
        cls.N_RESULTS = 10
        cls.CHUNK_SIZE = 512
        print("✅ All multi-modal features enabled")
    
    @classmethod
    def set_lightweight_mode(cls):
        """Set lightweight configuration for limited resources"""
        cls.ENABLE_TABLE_EXTRACTION = True
        cls.ENABLE_OCR = False
        cls.ENABLE_IMAGE_DESCRIPTION = False
        cls.N_RESULTS = 6
        cls.CHUNK_SIZE = 256
        cls.EMBEDDING_BATCH_SIZE = 16
        print("✅ Lightweight mode enabled")