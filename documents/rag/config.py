"""
Enhanced Configuration Settings for Multi-Modal RAG System
With support for general knowledge alongside document retrieval
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
    
    # General knowledge settings
    ALLOW_GENERAL_KNOWLEDGE = True  # Allow answers without document context
    STRICT_DOCUMENT_MODE = False  # Set True to only answer from documents
    INDICATE_KNOWLEDGE_SOURCE = False  # Whether to explicitly mention when using general knowledge
    
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
    
    # Main system prompt - supports both document retrieval and general knowledge
    SYSTEM_PROMPT = """You are a helpful AI assistant with access to specific documents and general knowledge.

HOW TO RESPOND:
- Answer questions naturally and conversationally, like talking to a colleague
- Be clear, direct, and helpful in your explanations
- Use simple language and avoid unnecessary jargon
- Maintain a friendly and approachable tone

USING DOCUMENT CONTEXT:
- When the Context section contains relevant information, incorporate it into your answer
- Present information directly and confidently
- Do NOT mention sources, documents, PDFs, page numbers, or where information came from
- Do NOT say things like "According to the document...", "The PDF shows...", "Looking at page X...", or "Based on the context..."
- Simply state the information as if it's knowledge you possess

USING GENERAL KNOWLEDGE:
- You can use your general knowledge to answer questions not covered in the documents
- You can provide background information, explanations, or related concepts
- You can combine document information with your general knowledge for comprehensive answers
- When a question clearly isn't about the specific documents, answer using your expertise

BALANCED APPROACH:
- If document context is provided and relevant, prioritize that information
- Supplement document information with general knowledge when helpful
- For questions requiring both specific and general information, combine them naturally
- Don't force document references if the question is general in nature

IF YOU DON'T KNOW:
- Be honest if you're uncertain about specific details
- Say something like "I don't have that specific information" or "I'm not certain about that"
- Don't make up facts or fabricate information

KEEP IT NATURAL:
- Never reference "the context", "the documents", "sources", or "PDFs" in your responses
- Present all information as direct knowledge
- Focus on being helpful and accurate

Remember: You're a knowledgeable assistant who can reference specific documents AND provide general expertise. Be natural, helpful, and conversational."""

    # Strict document-only mode prompt (when STRICT_DOCUMENT_MODE = True)
    STRICT_SYSTEM_PROMPT = """You are a helpful AI assistant that provides information strictly based on the provided documents.

HOW TO RESPOND:
- ONLY answer based on information in the Context section below
- Talk naturally and conversationally
- Present information directly without mentioning sources or documents
- Do NOT use phrases like "According to...", "The document shows...", etc.

STRICT RULES:
- If the Context section contains relevant information, use it to answer
- If the Context does NOT contain information to answer the question, clearly state:
  "I cannot find that information in the available documents"
- Do NOT use general knowledge or information outside the provided context
- Do NOT make assumptions or inferences beyond what's explicitly stated

PRESENTATION:
- Be clear and direct in your answers
- Use simple, natural language
- Never mention where the information comes from

Remember: You can ONLY use information from the Context section. If it's not there, say so."""

    # System prompt with source indication (when INDICATE_KNOWLEDGE_SOURCE = True)
    INDICATED_SYSTEM_PROMPT = """You are a helpful AI assistant with access to specific documents and general knowledge.

HOW TO RESPOND:
- Answer questions naturally and conversationally
- Be clear, direct, and helpful
- Use simple language

USING DOCUMENT INFORMATION:
- When using information from the provided Context section, present it directly
- Do NOT mention documents, PDFs, or page numbers
- Simply state the information naturally

USING GENERAL KNOWLEDGE:
- When answering with general knowledge (not from documents), briefly indicate this
- Use phrases like:
  * "While this isn't covered in the specific documents, I can explain that..."
  * "Based on general knowledge, ..."
  * "The documents don't specifically address this, but..."
- Keep these indicators brief and natural

COMBINED ANSWERS:
- You can combine document information with general knowledge
- Make it clear which parts come from documents vs. general knowledge
- Keep the distinction subtle and conversational

IF YOU DON'T KNOW:
- Be honest about uncertainty
- Don't make up information

Remember: Help users understand when you're using specific document information versus general knowledge."""

    # Query rewriting prompt
    REWRITE_SYSTEM_PROMPT = """Rewrite the follow-up question as a standalone question that includes necessary context from the conversation history.

Rules:
- Keep the rewritten question concise (1-2 sentences max)
- Include only essential context
- Maintain the original intent
- Output ONLY the rewritten question - no explanations
- If the question is already standalone, output it unchanged"""
    
    # Stop tokens
    STOP_TOKEN_IDS = [151645]
    
    # ==================== Response Mode Templates ====================
    
    # Template for when no context is found
    NO_CONTEXT_TEMPLATE = """Question: {question}

Please answer this question using your general knowledge. No specific document context is available for this query."""

    # Template for when context is available
    WITH_CONTEXT_TEMPLATE = """Context from documents:
{context}

Question: {question}

Please answer the question. Use the context if relevant, and you may also use your general knowledge to provide a complete answer."""

    # Template for strict mode with no context
    STRICT_NO_CONTEXT_RESPONSE = "I cannot find relevant information in the available documents to answer this question."
    
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
    def get_active_system_prompt(cls) -> str:
        """Get the appropriate system prompt based on current configuration"""
        if cls.STRICT_DOCUMENT_MODE:
            return cls.STRICT_SYSTEM_PROMPT
        elif cls.INDICATE_KNOWLEDGE_SOURCE:
            return cls.INDICATED_SYSTEM_PROMPT
        else:
            return cls.SYSTEM_PROMPT
    
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
            'device': cls.DEVICE or 'auto',
            'allow_general_knowledge': cls.ALLOW_GENERAL_KNOWLEDGE,
            'strict_document_mode': cls.STRICT_DOCUMENT_MODE,
            'indicate_knowledge_source': cls.INDICATE_KNOWLEDGE_SOURCE
        }
    
    @classmethod
    def enable_all_features(cls):
        """Enable all multi-modal features (requires more resources)"""
        cls.ENABLE_TABLE_EXTRACTION = True
        cls.ENABLE_OCR = True
        cls.ENABLE_IMAGE_DESCRIPTION = True
        cls.N_RESULTS = 10
        cls.CHUNK_SIZE = 512
        cls.ALLOW_GENERAL_KNOWLEDGE = True
        cls.STRICT_DOCUMENT_MODE = False
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
        cls.ALLOW_GENERAL_KNOWLEDGE = True
        print("✅ Lightweight mode enabled")
    
    @classmethod
    def enable_strict_mode(cls):
        """Enable strict document-only mode (no general knowledge)"""
        cls.STRICT_DOCUMENT_MODE = True
        cls.ALLOW_GENERAL_KNOWLEDGE = False
        cls.INDICATE_KNOWLEDGE_SOURCE = False
        print("✅ Strict document-only mode enabled")
        print("   System will only answer questions based on document content")
    
    @classmethod
    def enable_hybrid_mode(cls):
        """Enable hybrid mode (documents + general knowledge)"""
        cls.STRICT_DOCUMENT_MODE = False
        cls.ALLOW_GENERAL_KNOWLEDGE = True
        cls.INDICATE_KNOWLEDGE_SOURCE = False
        print("✅ Hybrid mode enabled")
        print("   System will use both documents and general knowledge")
    
    @classmethod
    def enable_indicated_mode(cls):
        """Enable mode with source indication"""
        cls.STRICT_DOCUMENT_MODE = False
        cls.ALLOW_GENERAL_KNOWLEDGE = True
        cls.INDICATE_KNOWLEDGE_SOURCE = True
        print("✅ Indicated mode enabled")
        print("   System will indicate when using general knowledge vs documents")
    
    @classmethod
    def set_similarity_threshold(cls, threshold: float):
        """
        Set the similarity threshold for document retrieval
        
        Args:
            threshold: Similarity threshold (0.0 to 1.0)
                      Lower = more lenient, Higher = more strict
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        
        cls.SIMILARITY_THRESHOLD = threshold
        print(f"✅ Similarity threshold set to {threshold}")
        
        if threshold < 0.3:
            print("   ⚠️  Very lenient - may include less relevant results")
        elif threshold > 0.7:
            print("   ⚠️  Very strict - may miss some relevant results")
    
    @classmethod
    def configure_for_use_case(cls, use_case: str):
        """
        Configure system for specific use cases
        
        Args:
            use_case: One of ['general_qa', 'strict_compliance', 'research', 'customer_support']
        """
        use_case = use_case.lower()
        
        if use_case == 'general_qa':
            # Balanced approach for general Q&A
            cls.enable_hybrid_mode()
            cls.SIMILARITY_THRESHOLD = 0.3
            cls.N_RESULTS = 6
            cls.TEMPERATURE = 0.3
            print("📋 Configured for: General Q&A")
            
        elif use_case == 'strict_compliance':
            # Strict mode for compliance/legal documents
            cls.enable_strict_mode()
            cls.SIMILARITY_THRESHOLD = 0.5
            cls.N_RESULTS = 8
            cls.TEMPERATURE = 0.1
            print("📋 Configured for: Strict Compliance")
            
        elif use_case == 'research':
            # Research mode with source indication
            cls.enable_indicated_mode()
            cls.SIMILARITY_THRESHOLD = 0.2
            cls.N_RESULTS = 10
            cls.TEMPERATURE = 0.2
            cls.ENABLE_RERANKING = True
            print("📋 Configured for: Research")
            
        elif use_case == 'customer_support':
            # Customer support with helpful general knowledge
            cls.enable_hybrid_mode()
            cls.SIMILARITY_THRESHOLD = 0.25
            cls.N_RESULTS = 5
            cls.TEMPERATURE = 0.4
            print("📋 Configured for: Customer Support")
            
        else:
            print(f"❌ Unknown use case: {use_case}")
            print("   Available: 'general_qa', 'strict_compliance', 'research', 'customer_support'")