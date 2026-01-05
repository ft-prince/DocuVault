"""
Enhanced RAG Chatbot with Multi-Modal Understanding and General Knowledge Support
Integrates all enhanced components for better document Q&A with flexible knowledge modes
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
    - General knowledge support with flexible modes
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
        
        # Show knowledge mode
        if self.config.STRICT_DOCUMENT_MODE:
            print(f"   📚 Mode: STRICT DOCUMENT-ONLY")
        elif self.config.INDICATE_KNOWLEDGE_SOURCE:
            print(f"   📚 Mode: HYBRID (with source indication)")
        else:
            print(f"   📚 Mode: HYBRID (documents + general knowledge)")
        
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
             use_hybrid: bool = None,
             allow_general_knowledge: bool = None,
             force_mode: str = None) -> Tuple[str, List[Dict]]:
        """
        Query the RAG system with a question
        
        Args:
            question: User question
            thread_id: Conversation thread ID
            n_results: Number of results to retrieve (default: config)
            use_rewrite: Whether to rewrite follow-up questions
            use_hybrid: Whether to use hybrid search (default: config)
            allow_general_knowledge: Override config for this query (True/False/None)
            force_mode: Force a specific mode for this query ('strict'/'hybrid'/'indicated'/None)
            
        Returns:
            Tuple of (answer, sources)
        """
        if not self.is_initialized:
            raise RuntimeError("System not initialized. Call initialize() first.")
        
        print("\n" + "="*70)
        print(f"💬 Query: {question}")
        print("="*70)
        
        start_time = time.time()
        
        # Determine operating mode for this query
        if force_mode:
            if force_mode == 'strict':
                use_strict_mode = True
                use_general_knowledge = False
                use_indicated_mode = False
            elif force_mode == 'indicated':
                use_strict_mode = False
                use_general_knowledge = True
                use_indicated_mode = True
            else:  # 'hybrid'
                use_strict_mode = False
                use_general_knowledge = True
                use_indicated_mode = False
        else:
            use_strict_mode = self.config.STRICT_DOCUMENT_MODE
            use_indicated_mode = self.config.INDICATE_KNOWLEDGE_SOURCE
            
            # Determine if general knowledge is allowed
            if allow_general_knowledge is not None:
                use_general_knowledge = allow_general_knowledge
            else:
                use_general_knowledge = self.config.ALLOW_GENERAL_KNOWLEDGE and not use_strict_mode
        
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
        
        # Determine system prompt based on mode
        if use_strict_mode:
            system_prompt = self.config.STRICT_SYSTEM_PROMPT
            mode_label = "STRICT"
        elif use_indicated_mode:
            system_prompt = self.config.INDICATED_SYSTEM_PROMPT
            mode_label = "INDICATED"
        else:
            system_prompt = self.config.SYSTEM_PROMPT
            mode_label = "HYBRID"
        
        print(f"🎯 Query mode: {mode_label}")
        
        # Prepare messages for LLM
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        # Add conversation history (limited)
        history_to_include = chat_history[-self.config.MAX_HISTORY_TURNS:]
        messages.extend(history_to_include)
        
        # Determine if we have relevant context
        has_relevant_context = False
        filtered_docs = []
        filtered_metas = []
        filtered_sims = []
        
        if documents:
            # Filter by similarity threshold
            for doc, meta, sim in zip(documents, metadatas, similarities):
                if sim >= self.config.SIMILARITY_THRESHOLD:
                    filtered_docs.append(doc)
                    filtered_metas.append(meta)
                    filtered_sims.append(sim)
            
            has_relevant_context = len(filtered_docs) > 0
        
        # Build user message based on context availability and mode
        if has_relevant_context:
            # We have relevant documents
            print(f"📄 Retrieved {len(filtered_docs)} relevant chunks (threshold: {self.config.SIMILARITY_THRESHOLD})")
            
            # Format context
            context = self.retriever.format_context_enhanced(filtered_docs, filtered_metas)
            
            # Use template with context
            user_message = self.config.WITH_CONTEXT_TEMPLATE.format(
                context=context,
                question=original_question
            )
            
            sources = self.retriever.prepare_sources_enhanced(
                filtered_docs,
                filtered_metas,
                filtered_sims
            )
            
        else:
            # No relevant context found
            print("⚠️  No relevant documents found")
            
            if use_strict_mode or not use_general_knowledge:
                # Strict mode or general knowledge disabled - cannot answer
                print("❌ Cannot answer without document context (strict mode)")
                
                # Still update conversation memory
                self._update_conversation_memory(
                    thread_id,
                    original_question,
                    self.config.STRICT_NO_CONTEXT_RESPONSE
                )
                
                return self.config.STRICT_NO_CONTEXT_RESPONSE, []
            
            else:
                # Use general knowledge
                print("💡 Using general knowledge")
                
                user_message = self.config.NO_CONTEXT_TEMPLATE.format(
                    question=original_question
                )
                
                sources = []
        
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
        
        # Update conversation memory
        self._update_conversation_memory(thread_id, original_question, answer)
        
        print(f"\n⏱️  Timing:")
        print(f"   Retrieval: {retrieval_time:.2f}s")
        print(f"   Generation: {generation_time:.2f}s")
        print(f"   Total: {total_time:.2f}s")
        print("="*70 + "\n")
        
        return answer, sources
    
    def _update_conversation_memory(self, thread_id: str, question: str, answer: str):
        """
        Update conversation memory for a thread
        
        Args:
            thread_id: Thread identifier
            question: User question
            answer: Assistant answer
        """
        if thread_id not in self.conversation_memory:
            self.conversation_memory[thread_id] = []
        
        self.conversation_memory[thread_id].append(
            {"role": "user", "content": question}
        )
        self.conversation_memory[thread_id].append(
            {"role": "assistant", "content": answer}
        )
        
        # Trim memory if too long
        if len(self.conversation_memory[thread_id]) > self.config.MAX_HISTORY_TURNS * 2:
            self.conversation_memory[thread_id] = \
                self.conversation_memory[thread_id][-self.config.MAX_HISTORY_TURNS * 2:]
    
    def query_strict(self, question: str, thread_id: str = "default", **kwargs) -> Tuple[str, List[Dict]]:
        """
        Query in strict document-only mode (convenience method)
        
        Args:
            question: User question
            thread_id: Conversation thread ID
            **kwargs: Additional arguments for query()
            
        Returns:
            Tuple of (answer, sources)
        """
        return self.query(question, thread_id=thread_id, force_mode='strict', **kwargs)
    
    def query_hybrid(self, question: str, thread_id: str = "default", **kwargs) -> Tuple[str, List[Dict]]:
        """
        Query in hybrid mode with general knowledge (convenience method)
        
        Args:
            question: User question
            thread_id: Conversation thread ID
            **kwargs: Additional arguments for query()
            
        Returns:
            Tuple of (answer, sources)
        """
        return self.query(question, thread_id=thread_id, force_mode='hybrid', **kwargs)
    
    def query_indicated(self, question: str, thread_id: str = "default", **kwargs) -> Tuple[str, List[Dict]]:
        """
        Query with source indication mode (convenience method)
        
        Args:
            question: User question
            thread_id: Conversation thread ID
            **kwargs: Additional arguments for query()
            
        Returns:
            Tuple of (answer, sources)
        """
        return self.query(question, thread_id=thread_id, force_mode='indicated', **kwargs)
    
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
    
    def set_mode(self, mode: str):
        """
        Set the operating mode for the chatbot
        
        Args:
            mode: One of 'strict', 'hybrid', or 'indicated'
        """
        mode = mode.lower()
        
        if mode == 'strict':
            self.config.enable_strict_mode()
        elif mode == 'hybrid':
            self.config.enable_hybrid_mode()
        elif mode == 'indicated':
            self.config.enable_indicated_mode()
        else:
            raise ValueError(f"Unknown mode: {mode}. Use 'strict', 'hybrid', or 'indicated'")
    
    def get_current_mode(self) -> str:
        """
        Get the current operating mode
        
        Returns:
            String describing current mode
        """
        if self.config.STRICT_DOCUMENT_MODE:
            return "strict (document-only)"
        elif self.config.INDICATE_KNOWLEDGE_SOURCE:
            return "indicated (hybrid with source indication)"
        else:
            return "hybrid (documents + general knowledge)"
    
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
            'active_threads': len(self.conversation_memory),
            'current_mode': self.get_current_mode(),
            'knowledge_settings': {
                'allow_general_knowledge': self.config.ALLOW_GENERAL_KNOWLEDGE,
                'strict_document_mode': self.config.STRICT_DOCUMENT_MODE,
                'indicate_knowledge_source': self.config.INDICATE_KNOWLEDGE_SOURCE
            }
        }
    
    def batch_query(self, questions: List[str], 
                   thread_id: str = "default",
                   mode: str = None) -> List[Tuple[str, List[Dict]]]:
        """
        Process multiple questions in sequence
        
        Args:
            questions: List of questions
            thread_id: Conversation thread ID
            mode: Optional mode override ('strict'/'hybrid'/'indicated')
            
        Returns:
            List of (answer, sources) tuples
        """
        results = []
        
        print(f"\n🔍 Processing {len(questions)} questions in batch...")
        if mode:
            print(f"   Mode: {mode}")
        
        for i, question in enumerate(questions, 1):
            print(f"\n[{i}/{len(questions)}]")
            
            if mode:
                answer, sources = self.query(question, thread_id=thread_id, force_mode=mode)
            else:
                answer, sources = self.query(question, thread_id=thread_id)
            
            results.append((answer, sources))
        
        return results
    
    def interactive_mode(self, thread_id: str = "default"):
        """
        Start an interactive chat session
        
        Args:
            thread_id: Conversation thread ID
        """
        print("\n" + "="*70)
        print("🤖 Interactive RAG Chat Mode")
        print("="*70)
        print(f"Current mode: {self.get_current_mode()}")
        print("\nCommands:")
        print("  'exit' or 'quit' - Exit interactive mode")
        print("  'clear' - Clear conversation memory")
        print("  'mode strict' - Switch to strict document-only mode")
        print("  'mode hybrid' - Switch to hybrid mode")
        print("  'mode indicated' - Switch to indicated mode")
        print("  'info' - Show system information")
        print("="*70 + "\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['exit', 'quit']:
                    print("\n👋 Goodbye!")
                    break
                
                elif user_input.lower() == 'clear':
                    self.clear_memory(thread_id)
                    continue
                
                elif user_input.lower().startswith('mode '):
                    mode = user_input[5:].strip()
                    try:
                        self.set_mode(mode)
                    except ValueError as e:
                        print(f"❌ {e}")
                    continue
                
                elif user_input.lower() == 'info':
                    info = self.get_system_info()
                    print("\n📊 System Information:")
                    print(f"   Mode: {info['current_mode']}")
                    print(f"   Documents in store: {info['vector_store']['total_documents']}")
                    print(f"   Active threads: {info['active_threads']}")
                    print(f"   LLM: {info['llm'].get('model_name', 'Unknown')}")
                    continue
                
                # Process as question
                answer, sources = self.query(user_input, thread_id=thread_id)
                
                print(f"\n🤖 Assistant: {answer}")
                
                if sources:
                    print(f"\n📚 Sources ({len(sources)}):")
                    for i, source in enumerate(sources[:3], 1):
                        print(f"   {i}. {source['source']} (page {source['page']}) - {source['content_type']}")
                
                print()
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                continue
    
    def export_conversation(self, thread_id: str = "default", format: str = "text") -> str:
        """
        Export conversation history
        
        Args:
            thread_id: Thread to export
            format: Export format ('text' or 'json')
            
        Returns:
            Formatted conversation string
        """
        history = self.get_conversation_history(thread_id)
        
        if format == "json":
            import json
            return json.dumps(history, indent=2)
        
        else:  # text format
            lines = []
            lines.append(f"Conversation Thread: {thread_id}")
            lines.append(f"Mode: {self.get_current_mode()}")
            lines.append("=" * 70)
            lines.append("")
            
            for msg in history:
                role = "User" if msg["role"] == "user" else "Assistant"
                lines.append(f"{role}: {msg['content']}")
                lines.append("")
            
            return "\n".join(lines)
    
    def get_statistics(self) -> Dict:
        """
        Get comprehensive statistics about the chatbot
        
        Returns:
            Dictionary with various statistics
        """
        total_conversations = sum(
            len(history) // 2 for history in self.conversation_memory.values()
        )
        
        return {
            'total_threads': len(self.conversation_memory),
            'total_conversations': total_conversations,
            'documents_indexed': self.vector_store.get_document_count() if self.vector_store else 0,
            'current_mode': self.get_current_mode(),
            'config_summary': self.config.get_config_summary()
        }