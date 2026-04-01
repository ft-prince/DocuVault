"""
Enhanced RAG Chatbot with Multi-Modal Understanding and General Knowledge Support
Integrates all enhanced components for better document Q&A with flexible knowledge modes
"""

from typing import List, Dict, Tuple, Optional
import sys
import time

from .config import RAGConfig


def _safe_print(*args, **kwargs):
    """Print with Unicode-safe fallback for Windows consoles."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        text = ' '.join(str(a) for a in args)
        print(text.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(
            sys.stdout.encoding or 'utf-8', errors='replace'), **kwargs)
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
        _safe_print("\n" + "="*70)
        _safe_print("🚀 Initializing Enhanced RAG System")
        _safe_print("="*70)
        
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
        
        _safe_print("\n✅ Enhanced RAG System initialized successfully!")
        _safe_print(f"   📊 Table extraction: {'Enabled' if self.config.ENABLE_TABLE_EXTRACTION else 'Disabled'}")
        _safe_print(f"   🔍 OCR: {'Enabled' if self.config.ENABLE_OCR else 'Disabled'}")
        _safe_print(f"   🖼️  Image description: {'Enabled' if self.config.ENABLE_IMAGE_DESCRIPTION else 'Disabled'}")
        _safe_print(f"   🔀 Hybrid search: {'Enabled' if self.config.USE_HYBRID_SEARCH else 'Disabled'}")
        
        # Show knowledge mode
        if self.config.STRICT_DOCUMENT_MODE:
            _safe_print(f"   📚 Mode: STRICT DOCUMENT-ONLY")
        elif self.config.INDICATE_KNOWLEDGE_SOURCE:
            _safe_print(f"   📚 Mode: HYBRID (with source indication)")
        else:
            _safe_print(f"   📚 Mode: HYBRID (documents + general knowledge)")
        
        _safe_print("="*70 + "\n")
    
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
        
        _safe_print("\n" + "="*70)
        _safe_print("📚 Starting Document Indexing")
        _safe_print("="*70)
        
        start_time = time.time()
        
        # Process documents
        if pdf_path:
            _safe_print(f"Processing PDF: {pdf_path}")
            chunks = self.document_processor.process_document_complete(
                pdf_path=pdf_path,
                extract_tables=extract_tables,
                describe_images=describe_images
            )
        elif documents:
            _safe_print(f"Processing {len(documents)} pre-loaded documents")
            chunks = self.document_processor.split_documents_smart(documents)
        else:
            raise ValueError("Either pdf_path or documents must be provided")
        
        if not chunks:
            _safe_print("⚠️  No chunks created from documents")
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
        
        _safe_print(f"\n✅ Indexing completed in {processing_time:.2f}s")
        _safe_print(f"   📦 Total chunks in vector store: {self.vector_store.get_document_count()}")
        
        # Show processing stats
        stats = self.document_processor.get_processing_stats()
        if stats['total_pages'] > 0:
            _safe_print(f"\n📊 Processing Statistics:")
            _safe_print(f"   Total pages: {stats['total_pages']}")
            _safe_print(f"   Text pages: {stats['text_pages']}")
            _safe_print(f"   OCR pages: {stats['ocr_pages']}")
            _safe_print(f"   Tables extracted: {stats['tables_extracted']}")
            _safe_print(f"   Images processed: {stats['images_processed']}")
        
        _safe_print("="*70 + "\n")
    
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
        
        _safe_print("\n" + "="*70)
        _safe_print(f"💬 Query: {question}")
        _safe_print("="*70)
        
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
                _safe_print(f"🔄 Rewritten query: {question}")
        
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
        
        _safe_print(f"🎯 Query mode: {mode_label}")
        
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
            top_score = filtered_sims[0] if filtered_sims else self.config.SIMILARITY_THRESHOLD
            strong = top_score >= self.config.STRONG_CONTEXT_THRESHOLD
            _safe_print(f"📄 Retrieved {len(filtered_docs)} chunks (top score: {top_score:.3f}, strong: {strong})")

            if strong or use_strict_mode:
                # Context is directly on-topic — use it as the main source
                context = self.retriever.format_context_enhanced(filtered_docs, filtered_metas)
                user_message = self.config.WITH_CONTEXT_TEMPLATE.format(
                    context=context,
                    question=original_question
                )
                sources = self.retriever.prepare_sources_enhanced(
                    filtered_docs, filtered_metas, filtered_sims
                )
            elif use_general_knowledge:
                # Context is only tangentially relevant — drop it, answer from pure GK
                _safe_print("⚠️  Weak context (top score below STRONG threshold) — switching to pure GK")
                user_message = self.config.NO_CONTEXT_TEMPLATE.format(question=original_question)
                sources = []
            else:
                context = self.retriever.format_context_enhanced(filtered_docs, filtered_metas)
                user_message = self.config.WITH_CONTEXT_TEMPLATE.format(
                    context=context,
                    question=original_question
                )
                sources = self.retriever.prepare_sources_enhanced(
                    filtered_docs, filtered_metas, filtered_sims
                )
            
        else:
            # No relevant context found
            _safe_print("⚠️  No relevant documents found")
            
            if use_strict_mode or not use_general_knowledge:
                # Strict mode or general knowledge disabled - cannot answer
                _safe_print("❌ Cannot answer without document context (strict mode)")
                
                # Still update conversation memory
                self._update_conversation_memory(
                    thread_id,
                    original_question,
                    self.config.STRICT_NO_CONTEXT_RESPONSE
                )
                
                return self.config.STRICT_NO_CONTEXT_RESPONSE, []
            
            else:
                # Use general knowledge
                _safe_print("💡 Using general knowledge")
                
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
        
        _safe_print(f"\n⏱️  Timing:")
        _safe_print(f"   Retrieval: {retrieval_time:.2f}s")
        _safe_print(f"   Generation: {generation_time:.2f}s")
        _safe_print(f"   Total: {total_time:.2f}s")
        _safe_print("="*70 + "\n")
        
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
    
    # ── Hinglish word list (Latin-script Hindi stop/content words) ────
    _HINDI_LATIN = frozenset([
        # Postpositions / case markers
        'ka','ki','ke','se','ko','par','mein','tak','liye','bina','saath',
        # Pronouns
        'main','hum','tum','aap','wo','woh','ye','yeh','isko','usko',
        'inhe','unhe','mere','mera','meri','teri','tera','uska',
        'uski','unka','unki','humara','humari','tumhara','tumhari',
        # Verbs / verb forms
        # NOTE: 'the' and 'to' removed — they are common English words and cause
        # false-positive Hinglish detection on virtually every English sentence.
        'hai','hain','tha','thi','hoga','hogi','hoge','hote','hoti',
        'karna','karta','karti','karte','karo','kiya','karke',
        'jana','jata','jati','jao','gaya','gayi','gaye',
        'aana','aata','aati','aao','aya','ayi','aaye',
        'lena','leta','leti','liya',
        'dena','deta','deti','diya',
        'bolna','bolta','bolti','bolo','bola','boli',
        'dekhna','dekhta','dekhti','dekho','dekha','dekhi',
        'rehna','rehta','rehti','raho','raha','rahi',
        'milna','milta','milti','milo','mila','mili',
        'chahna','chahta','chahti','chahiye',
        'padhna','likhna','sunna','samajhna',
        'lagta','lagti','laga','lagi',
        'pata','nikla','nikli','bana','bani',
        # Question words
        'kya','kaun','kahan','kab','kaise','kyun','kyunki','kitna','kitne','kitni',
        # Conjunctions / connectors
        'aur','lekin','magar','toh','phir','isliye','warna',
        'jabki','jabse','jaise','waisa',
        # Adverbs / modifiers
        'bhi','hi','nahi','nahin','mat','haan','ji','bilkul','zaroor',
        'shayad','hamesha','kabhi','abhi','abtak','baad','pehle','sirf',
        'bahut','zyada','jyada','thoda','kam','seedha','aksar',
        # Common nouns (Hinglish context)
        'kaam','kaamkaaj','khabar','baat','cheez','jagah','waqt','samay',
        'paisa','kitab','ghar','desh','aadmi','aurat','baccha',
        'raat','saal','mahina','hafta',
        # Discourse / interjections
        'acha','accha','theek','sahi','galat','matlab','samajh',
        'batao','suno','suniye','samjhe',
        'yahan','wahan','idhar','udhar','agar','jab','tab',
    ])

    # ── Multilingual helpers ────────────────────────────────────────────

    _NON_ASCII_SCRIPTS = (
        # Devanagari (Hindi, Marathi, Sanskrit)
        (0x0900, 0x097F),
        # Bengali
        (0x0980, 0x09FF),
        # Gujarati
        (0x0A80, 0x0AFF),
        # Gurmukhi (Punjabi)
        (0x0A00, 0x0A7F),
        # Tamil
        (0x0B80, 0x0BFF),
        # Telugu
        (0x0C00, 0x0C7F),
        # Kannada
        (0x0C80, 0x0CFF),
        # Malayalam
        (0x0D00, 0x0D7F),
        # Arabic / Urdu
        (0x0600, 0x06FF),
        # CJK / Chinese / Japanese / Korean
        (0x4E00, 0x9FFF),
    )

    def _is_non_english(self, text: str) -> bool:
        """Return True if more than 15 % of chars are from a non-Latin script."""
        if not text:
            return False
        count = 0
        for ch in text:
            cp = ord(ch)
            for lo, hi in self._NON_ASCII_SCRIPTS:
                if lo <= cp <= hi:
                    count += 1
                    break
        return count / max(len(text), 1) > 0.15

    def _is_hinglish(self, text: str) -> bool:
        """
        Detect Hinglish: Latin-script Hindi words mixed with English.
        e.g. 'AquaFlow ka CEO kaun hai' — all ASCII but contains Hindi tokens.
        Returns True if ≥ 1 Hindi word found AND they form >10% of total words.
        """
        words = [w.strip('?.,!').lower() for w in text.split() if w.strip('?.,!')]
        if not words:
            return False
        hindi_count = sum(1 for w in words if w in self._HINDI_LATIN)
        return hindi_count >= 1 and (hindi_count / len(words)) > 0.10

    @staticmethod
    def _is_latin(text: str) -> bool:
        """Return True if >70% of alphabetic chars are ASCII/Latin (i.e. the text is English)."""
        alpha = [c for c in text if c.isalpha()]
        if not alpha:
            return True
        ascii_count = sum(1 for c in alpha if ord(c) < 128)
        return (ascii_count / len(alpha)) > 0.70

    def _translate_for_retrieval(self, text: str) -> str:
        """
        Translate a non-English query to English for embedding/retrieval.
        Uses a minimal LLM call — only translation, not answering.
        If the result is not Latin-script (translation failed), falls back to
        a keyword extraction approach so retrieval still gets something useful.
        """
        try:
            msgs = [
                {
                    "role": "system",
                    "content": (
                        "Translate the following text to English. "
                        "Output ONLY the English translation — no explanations, "
                        "no punctuation changes, nothing else."
                    ),
                },
                {"role": "user", "content": text},
            ]
            translated = self.llm_manager.generate(
                messages=msgs,
                max_new_tokens=120,
                temperature=0.05,
            )
            result = translated.strip() if translated else ''
            _safe_print(f"🌐 Translated for retrieval: '{result}'")
            # Validate: result must be non-empty and in Latin script
            if result and self._is_latin(result):
                return result
            # Translation returned non-Latin text (e.g. Devanagari) → fallback
            _safe_print("⚠️  Translation output is non-Latin — using original text for retrieval")
            return text
        except Exception as e:
            _safe_print(f"⚠️  Translation failed, using original: {e}")
            return text

    # ── Streaming query ────────────────────────────────────────────────

    # Maps BCP-47 language codes → readable names for LLM translate instructions
    _LANG_NAMES = {
        'hi-IN': 'Hindi', 'ta-IN': 'Tamil', 'te-IN': 'Telugu',
        'bn-IN': 'Bengali', 'mr-IN': 'Marathi', 'gu-IN': 'Gujarati',
        'kn-IN': 'Kannada', 'ml-IN': 'Malayalam', 'pa-IN': 'Punjabi',
        'ur-IN': 'Urdu', 'en-IN': 'English', 'en-US': 'English',
    }

    def query_stream(self, question: str, thread_id: str = "default",
                    n_results: int = None, use_rewrite: bool = True,
                    use_hybrid: bool = None, reply_lang: str = None):
        """
        Stream the response token by token using SSE-style generator.

        Yields dicts:
          {"type": "sources", "data": [source, ...]}   — emitted once, before any tokens
          {"type": "token",   "data": "word "}          — one per LLM chunk
          {"type": "done",    "data": full_answer_str}  — emitted last
          {"type": "error",   "data": error_message}    — on exception
        """
        if not self.is_initialized:
            yield {"type": "error", "data": "RAG system not initialized"}
            return

        try:
            chat_history = self.conversation_memory.get(thread_id, [])
            original_question = question

            # ── Multilingual / Hinglish: translate to English for retrieval ──
            # _is_non_english detects Devanagari/Tamil/etc. (Unicode scripts)
            # _is_hinglish  detects Latin-script Hindi ("ka CEO kaun hai")
            is_multilingual = self._is_non_english(question) or self._is_hinglish(question)
            retrieval_question = (
                self._translate_for_retrieval(question) if is_multilingual else question
            )

            # Rewrite follow-up questions (use translated version for retrieval)
            if use_rewrite and chat_history:
                retrieval_question = self.retriever.rewrite_query(retrieval_question, chat_history)

            # Retrieve relevant chunks using the English form of the query
            n_results = n_results or self.config.N_RESULTS
            use_hybrid = use_hybrid if use_hybrid is not None else self.config.USE_HYBRID_SEARCH

            documents, metadatas, similarities = self.retriever.retrieve(
                query=retrieval_question, n_results=n_results, use_hybrid=use_hybrid
            )

            # Filter by similarity threshold
            filtered_docs, filtered_metas, filtered_sims = [], [], []
            for doc, meta, sim in zip(documents, metadatas, similarities):
                if sim >= self.config.SIMILARITY_THRESHOLD:
                    filtered_docs.append(doc)
                    filtered_metas.append(meta)
                    filtered_sims.append(sim)

            has_context = len(filtered_docs) > 0

            # Determine if context is strong (directly relevant) or weak (tangential)
            if has_context:
                top_score = filtered_sims[0]
                strong_context = top_score >= self.config.STRONG_CONTEXT_THRESHOLD
                _safe_print(f"[stream] top_score={top_score:.3f} strong={strong_context}")
            else:
                strong_context = False

            # For weak context in hybrid mode, treat as no-context so GK is used cleanly
            if has_context and not strong_context and self.config.ALLOW_GENERAL_KNOWLEDGE and not self.config.STRICT_DOCUMENT_MODE:
                _safe_print("[stream] Weak context — dropping docs, using GK")
                has_context = False
                filtered_docs, filtered_metas, filtered_sims = [], [], []

            sources = (
                self.retriever.prepare_sources_enhanced(filtered_docs, filtered_metas, filtered_sims)
                if has_context else []
            )

            # Emit sources immediately so the client can display them right away
            yield {"type": "sources", "data": sources}

            # Build LLM messages — always use ORIGINAL question so response is in user's language
            system_prompt = self.config.get_active_system_prompt()

            # Inject language instruction when query is non-English
            if is_multilingual:
                system_prompt = (
                    "MULTILINGUAL INSTRUCTION — READ CAREFULLY:\n"
                    "• The document context below is written in English.\n"
                    "• The user has asked their question in Hindi, Hinglish, or another Indian language.\n"
                    "• You MUST answer in the EXACT same language/script the user used.\n"
                    "• You MUST extract facts from the English context and express them in the user's language.\n"
                    "• NEVER say 'I don't know' or 'mujhe pata nahi' if the context contains the answer.\n"
                    "• NEVER answer from general knowledge when English context is provided — "
                    "translate and summarise the context facts instead.\n"
                    "• CRITICAL: Do NOT confuse different characters or people in the context. "
                    "Each person has their own role/attributes — do NOT apply one person's details to another.\n"
                    "• CRITICAL: If the context does NOT contain the specific information asked, "
                    "say so honestly in the user's language. Do NOT infer, guess, or hallucinate details "
                    "that are not explicitly written in the context.\n\n"
                ) + system_prompt

            # ── Translate mode: user spoke English but wants reply in another language ──
            elif reply_lang and reply_lang not in ('en-IN', 'en-US', 'en'):
                target = self._LANG_NAMES.get(reply_lang, reply_lang)
                system_prompt = (
                    f"TRANSLATE MODE — CRITICAL INSTRUCTION:\n"
                    f"• The user spoke in English.\n"
                    f"• You MUST write your ENTIRE response in {target}.\n"
                    f"• Do NOT include any English text in your response — translate everything to {target}.\n"
                    f"• CRITICAL: Do NOT confuse different characters/people. "
                    f"Each person has their own role — do NOT mix up attributes between different people.\n"
                    f"• If document context is provided, summarise and translate ONLY what is explicitly "
                    f"stated in the context — do NOT guess or add information not present.\n"
                    f"• If the document context does NOT contain the answer, say clearly in {target} that "
                    f"the information is not available in the provided documents.\n"
                    f"• Answer naturally and conversationally in {target}.\n\n"
                ) + system_prompt

            # ── English mode: enforce English even if session history has other languages ──
            elif not is_multilingual:
                system_prompt = (
                    "LANGUAGE INSTRUCTION: Reply in English only. "
                    "Do NOT use Hindi or any other language, regardless of previous conversation.\n\n"
                ) + system_prompt

            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(chat_history[-self.config.MAX_HISTORY_TURNS:])

            if has_context:
                context = self.retriever.format_context_enhanced(filtered_docs, filtered_metas)
                if is_multilingual:
                    # Explicit bilingual scaffold for Hindi/Hinglish answers
                    user_msg = (
                        "=== DOCUMENT CONTEXT (English) ===\n"
                        f"{context}\n\n"
                        "=== USER QUESTION ===\n"
                        f"{original_question}\n\n"
                        "TASK: Using ONLY the information explicitly written in the document context above, "
                        "answer the question. Write your answer in the same language as the question "
                        "(Hindi or Hinglish if the question is in those languages). "
                        "If the context DOES contain the answer, extract it and translate it — do not "
                        "add details not in the context. "
                        "If the context does NOT contain the answer to the question, say clearly in the "
                        "user's language that this specific information is not in the documents."
                    )
                elif reply_lang and reply_lang not in ('en-IN', 'en-US', 'en'):
                    # Translate mode + context: strict bilingual scaffold
                    target = self._LANG_NAMES.get(reply_lang, reply_lang)
                    user_msg = (
                        "=== DOCUMENT CONTEXT (English) ===\n"
                        f"{context}\n\n"
                        "=== USER QUESTION ===\n"
                        f"{original_question}\n\n"
                        f"TASK: Using ONLY the information explicitly written in the document context "
                        f"above, answer the question. Write your ENTIRE answer in {target}. "
                        f"Extract and translate facts from the context — do NOT add details not in the "
                        f"context. If the context does NOT contain the answer, say clearly in {target} "
                        f"that this information is not available in the documents."
                    )
                else:
                    user_msg = self.config.WITH_CONTEXT_TEMPLATE.format(
                        context=context, question=original_question
                    )
            else:
                if self.config.STRICT_DOCUMENT_MODE:
                    answer = self.config.STRICT_NO_CONTEXT_RESPONSE
                    yield {"type": "token", "data": answer}
                    yield {"type": "done", "data": answer}
                    self._update_conversation_memory(thread_id, original_question, answer)
                    return
                else:
                    # No relevant docs (or weak context dropped) — answer from general knowledge
                    user_msg = self.config.NO_CONTEXT_TEMPLATE.format(question=original_question)

            messages.append({"role": "user", "content": user_msg})

            # Stream tokens
            full_answer = ""
            for token in self.llm_manager.generate_stream(
                messages,
                max_new_tokens=self.config.MAX_NEW_TOKENS,
                temperature=self.config.TEMPERATURE,
            ):
                full_answer += token
                yield {"type": "token", "data": token}

            # Persist to memory and signal completion
            self._update_conversation_memory(thread_id, original_question, full_answer)
            yield {"type": "done", "data": full_answer}

        except Exception as exc:
            yield {"type": "error", "data": str(exc)}

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
                _safe_print(f"🗑️  Cleared memory for thread: {thread_id}")
        else:
            self.conversation_memory.clear()
            _safe_print("🗑️  Cleared all conversation memory")
    
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
        
        _safe_print(f"\n🔍 Processing {len(questions)} questions in batch...")
        if mode:
            _safe_print(f"   Mode: {mode}")
        
        for i, question in enumerate(questions, 1):
            _safe_print(f"\n[{i}/{len(questions)}]")
            
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
        _safe_print("\n" + "="*70)
        _safe_print("🤖 Interactive RAG Chat Mode")
        _safe_print("="*70)
        _safe_print(f"Current mode: {self.get_current_mode()}")
        _safe_print("\nCommands:")
        _safe_print("  'exit' or 'quit' - Exit interactive mode")
        _safe_print("  'clear' - Clear conversation memory")
        _safe_print("  'mode strict' - Switch to strict document-only mode")
        _safe_print("  'mode hybrid' - Switch to hybrid mode")
        _safe_print("  'mode indicated' - Switch to indicated mode")
        _safe_print("  'info' - Show system information")
        _safe_print("="*70 + "\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['exit', 'quit']:
                    _safe_print("\n👋 Goodbye!")
                    break
                
                elif user_input.lower() == 'clear':
                    self.clear_memory(thread_id)
                    continue
                
                elif user_input.lower().startswith('mode '):
                    mode = user_input[5:].strip()
                    try:
                        self.set_mode(mode)
                    except ValueError as e:
                        _safe_print(f"❌ {e}")
                    continue
                
                elif user_input.lower() == 'info':
                    info = self.get_system_info()
                    _safe_print("\n📊 System Information:")
                    _safe_print(f"   Mode: {info['current_mode']}")
                    _safe_print(f"   Documents in store: {info['vector_store']['total_documents']}")
                    _safe_print(f"   Active threads: {info['active_threads']}")
                    _safe_print(f"   LLM: {info['llm'].get('model_name', 'Unknown')}")
                    continue
                
                # Process as question
                answer, sources = self.query(user_input, thread_id=thread_id)
                
                _safe_print(f"\n🤖 Assistant: {answer}")
                
                if sources:
                    _safe_print(f"\n📚 Sources ({len(sources)}):")
                    for i, source in enumerate(sources[:3], 1):
                        _safe_print(f"   {i}. {source['source']} (page {source['page']}) - {source['content_type']}")
                
                _safe_print()
                
            except KeyboardInterrupt:
                _safe_print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                _safe_print(f"\n❌ Error: {e}")
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