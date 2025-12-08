"""
Enhanced RAG Chatbot with Multi-Modal Understanding
Integrates all enhanced components for better document Q&A
"""

from typing import List, Dict, Tuple, Optional
import time

from .config import RAGConfig
from .document_processor import EnhancedDocumentProcessor
from .embeddings import EnhancedEmbeddingManager
from .vector_store import VectorStore
from .llm_manager import LLMManager
from .retriever import EnhancedRetriever


class RAGChatbot:
    """
    Enhanced RAG Chatbot with:
    - Multi-modal document understanding (text, tables, images)
    - Hybrid search (semantic + keyword)
    - Better context formatting
    - Improved conversation memory
    """
    
    def __init__(self, config: RAGConfig = None):
        """
        Initialize enhanced RAG chatbot
        
        Args:
            config: Enhanced RAG configuration
        """
        self.config = config or RAGConfig()
        
        # Initialize components
        self.document_processor = EnhancedDocumentProcessor(self.config)
        self.embedding_manager = EnhancedEmbeddingManager(self.config)
        self.vector_store = VectorStore(self.config)
        self.llm_manager = LLMManager(self.config)
        self.retriever = None  # Initialized after vector store
        
        # Conversation memory by thread
        self.conversation_memory = {}
        
        # System status
        self.is_initialized = False
    
    def initialize(self, db_path: str = None, reset: bool = False):
        """
        Initialize all components
        
        Args:
            db_path: Path for ChromaDB storage
            reset: Whether to reset the vector store
        """
        print("\n" + "="*70)
        print("🚀 Initializing Enhanced RAG System")
        print("="*70)
        
        # Set ChromaDB path
        if db_path:
            self.config.set_chroma_path(db_path)
        
        # Initialize vector store
        self.vector_store.initialize(reset=reset)
        
        # Load embedding model
        self.embedding_manager.load_model()
        
        # Load LLM
        self.llm_manager.load_model()
        
        # Initialize retriever
        self.retriever = EnhancedRetriever(
            embedding_manager=self.embedding_manager,
            vector_store=self.vector_store,
            llm_manager=self.llm_manager,
            config=self.config
        )
        
        self.is_initialized = True
        
        print("\n✅ Enhanced RAG System initialized successfully!")
        print(f"   📊 Table extraction: {'Enabled' if self.config.ENABLE_TABLE_EXTRACTION else 'Disabled'}")
        print(f"   🔍 OCR: {'Enabled' if self.config.ENABLE_OCR else 'Disabled'}")
        print(f"   🖼️  Image description: {'Enabled' if self.config.ENABLE_IMAGE_DESCRIPTION else 'Disabled'}")
        print(f"   🔀 Hybrid search: {'Enabled' if self.config.USE_HYBRID_SEARCH else 'Disabled'}")
        print("="*70 + "\n")
    
    def index_documents(self, pdf_path: str = None, documents: List = None,
                       extract_tables: bool = None,
                       describe_images: bool = None):
        """
        Index documents with enhanced processing
        
        Args:
            pdf_path: Path to single PDF file
            documents: Pre-loaded LangChain documents
            extract_tables: Override config for table extraction
            describe_images: Override config for image description
        """
        if not self.is_initialized:
            raise RuntimeError("System not initialized. Call initialize() first.")
        
        extract_tables = extract_tables if extract_tables is not None else self.config.ENABLE_TABLE_EXTRACTION
        describe_images = describe_images if describe_images is not None else self.config.ENABLE_IMAGE_DESCRIPTION
        
        print("\n" + "="*70)
        print("📚 Starting Document Indexing")
        print("="*70)
        
        start_time = time.time()
        
        # Process documents
        if pdf_path:
            print(f"Processing PDF: {pdf_path}")
            chunks = self.document_processor.process_document_complete(
                pdf_path=pdf_path,
                extract_tables=extract_tables,
                describe_images=describe_images
            )
        elif documents:
            print(f"Processing {len(documents)} pre-loaded documents")
            chunks = self.document_processor.split_documents_smart(documents)
        else:
            raise ValueError("Either pdf_path or documents must be provided")
        
        if not chunks:
            print("⚠️  No chunks created from documents")
            return
        
        # Prepare for embedding
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        chunk_types = [meta.get('chunk_type', 'text') for meta in metadatas]
        
        # Generate embeddings with preprocessing
        embeddings = self.embedding_manager.generate_embeddings_enhanced(
            texts=texts,
            chunk_types=chunk_types,
            show_progress=True
        )
        
        # Generate unique IDs
        ids = [
            f"{meta.get('source', 'doc')}_{meta.get('page', 0)}_{meta.get('chunk_index', i)}"
            for i, meta in enumerate(metadatas)
        ]
        
        # Add to vector store
        self.vector_store.add_documents(
            embeddings=embeddings.tolist(),
            texts=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        processing_time = time.time() - start_time
        
        print(f"\n✅ Indexing completed in {processing_time:.2f}s")
        print(f"   📦 Total chunks in vector store: {self.vector_store.get_document_count()}")
        
        # Show processing stats
        stats = self.document_processor.get_processing_stats()
        if stats['total_pages'] > 0:
            print(f"\n📊 Processing Statistics:")
            print(f"   Total pages: {stats['total_pages']}")
            print(f"   Text pages: {stats['text_pages']}")
            print(f"   OCR pages: {stats['ocr_pages']}")
            print(f"   Tables extracted: {stats['tables_extracted']}")
            print(f"   Images processed: {stats['images_processed']}")
        
        print("="*70 + "\n")
    
    def query(self, question: str, 
             thread_id: str = "default",
             n_results: int = None,
             use_rewrite: bool = True,
             use_hybrid: bool = None) -> Tuple[str, List[Dict]]:
        """
        Query the RAG system with a question
        
        Args:
            question: User question
            thread_id: Conversation thread ID
            n_results: Number of results to retrieve (default: config)
            use_rewrite: Whether to rewrite follow-up questions
            use_hybrid: Whether to use hybrid search (default: config)
            
        Returns:
            Tuple of (answer, sources)
        """
        if not self.is_initialized:
            raise RuntimeError("System not initialized. Call initialize() first.")
        
        print("\n" + "="*70)
        print(f"💬 Query: {question}")
        print("="*70)
        
        start_time = time.time()
        
        # Get conversation history
        chat_history = self.conversation_memory.get(thread_id, [])
        
        # Rewrite query if it's a follow-up
        original_question = question
        if use_rewrite and chat_history:
            question = self.retriever.rewrite_query(question, chat_history)
            if question != original_question:
                print(f"🔄 Rewritten query: {question}")
        
        # Retrieve relevant documents
        n_results = n_results or self.config.N_RESULTS
        use_hybrid = use_hybrid if use_hybrid is not None else self.config.USE_HYBRID_SEARCH
        
        documents, metadatas, similarities = self.retriever.retrieve(
            query=question,
            n_results=n_results,
            use_hybrid=use_hybrid
        )
        
        retrieval_time = time.time() - start_time
        
        if not documents:
            print("⚠️  No relevant documents found")
            return "I cannot find any relevant information in the documents.", []
        
        # Filter by similarity threshold
        filtered_docs = []
        filtered_metas = []
        filtered_sims = []
        
        for doc, meta, sim in zip(documents, metadatas, similarities):
            if sim >= self.config.SIMILARITY_THRESHOLD:
                filtered_docs.append(doc)
                filtered_metas.append(meta)
                filtered_sims.append(sim)
        
        if not filtered_docs:
            print(f"⚠️  No documents above similarity threshold ({self.config.SIMILARITY_THRESHOLD})")
            return "I cannot find sufficiently relevant information in the documents.", []
        
        print(f"📄 Retrieved {len(filtered_docs)} relevant chunks (threshold: {self.config.SIMILARITY_THRESHOLD})")
        
        # Format context
        context = self.retriever.format_context_enhanced(filtered_docs, filtered_metas)
        
        # Prepare messages for LLM
        messages = [
            {"role": "system", "content": self.config.SYSTEM_PROMPT},
        ]
        
        # Add conversation history (limited)
        history_to_include = chat_history[-self.config.MAX_HISTORY_TURNS:]
        messages.extend(history_to_include)
        
        # Add current query with context
        user_message = f"""Here's what I found in the documents:
{context}

Now, the user is asking: {original_question}

Please answer their question naturally, like you're helping a colleague."""
        
        messages.append({"role": "user", "content": user_message})
        
        # Generate answer
        gen_start = time.time()
        answer = self.llm_manager.generate(
            messages=messages,
            max_new_tokens=self.config.MAX_NEW_TOKENS,
            temperature=self.config.TEMPERATURE
        )
        generation_time = time.time() - gen_start
        
        total_time = time.time() - start_time
        
        # Prepare sources
        sources = self.retriever.prepare_sources_enhanced(
            filtered_docs,
            filtered_metas,
            filtered_sims
        )
        
        # Update conversation memory
        if thread_id not in self.conversation_memory:
            self.conversation_memory[thread_id] = []
        
        self.conversation_memory[thread_id].append(
            {"role": "user", "content": original_question}
        )
        self.conversation_memory[thread_id].append(
            {"role": "assistant", "content": answer}
        )
        
        # Trim memory if too long
        if len(self.conversation_memory[thread_id]) > self.config.MAX_HISTORY_TURNS * 2:
            self.conversation_memory[thread_id] = \
                self.conversation_memory[thread_id][-self.config.MAX_HISTORY_TURNS * 2:]
        
        print(f"\n⏱️  Timing:")
        print(f"   Retrieval: {retrieval_time:.2f}s")
        print(f"   Generation: {generation_time:.2f}s")
        print(f"   Total: {total_time:.2f}s")
        print("="*70 + "\n")
        
        return answer, sources
    
    def clear_memory(self, thread_id: str = None):
        """
        Clear conversation memory
        
        Args:
            thread_id: Specific thread to clear (or None for all)
        """
        if thread_id:
            if thread_id in self.conversation_memory:
                del self.conversation_memory[thread_id]
                print(f"🗑️  Cleared memory for thread: {thread_id}")
        else:
            self.conversation_memory.clear()
            print("🗑️  Cleared all conversation memory")
    
    def get_conversation_history(self, thread_id: str = "default") -> List[Dict]:
        """Get conversation history for a thread"""
        return self.conversation_memory.get(thread_id, [])
    
    def get_system_info(self) -> Dict:
        """Get system information and statistics"""
        llm_info = self.llm_manager.get_model_info() if self.llm_manager else {}
        
        return {
            'initialized': self.is_initialized,
            'config': self.config.get_config_summary(),
            'vector_store': {
                'total_documents': self.vector_store.get_document_count() if self.vector_store else 0,
                'collection_name': self.config.COLLECTION_NAME
            },
            'llm': llm_info,
            'embedding_dimension': self.embedding_manager.get_embedding_dimension() if self.embedding_manager else 0,
            'active_threads': len(self.conversation_memory)
        }
    
    def batch_query(self, questions: List[str], thread_id: str = "default") -> List[Tuple[str, List[Dict]]]:
        """
        Process multiple questions in sequence
        
        Args:
            questions: List of questions
            thread_id: Conversation thread ID
            
        Returns:
            List of (answer, sources) tuples
        """
        results = []
        
        print(f"\n📝 Processing {len(questions)} questions in batch...")
        
        for i, question in enumerate(questions, 1):
            print(f"\n[{i}/{len(questions)}]")
            answer, sources = self.query(question, thread_id=thread_id)
            results.append((answer, sources))
        
        return results