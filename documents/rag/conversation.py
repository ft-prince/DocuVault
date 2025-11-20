"""
Conversation management with memory for RAG chatbot
"""

from typing import List, Dict, Tuple, Optional
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage

from .config import RAGConfig
from .embeddings import EmbeddingManager
from .vector_store import VectorStore
from .llm_manager import LLMManager
from .retriever import Retriever


class RAGChatbot:
    """Main RAG chatbot with conversation memory and hallucination prevention"""
    
    def __init__(self, config: RAGConfig = None):
        """
        Initialize RAG chatbot
        
        Args:
            config: RAGConfig instance. If None, uses default.
        """
        self.config = config or RAGConfig()
        
        # Initialize components
        self.embedding_manager = EmbeddingManager(config=self.config)
        self.vector_store = VectorStore(config=self.config)
        self.llm_manager = LLMManager(config=self.config)
        self.retriever = Retriever(
            embedding_manager=self.embedding_manager,
            vector_store=self.vector_store,
            llm_manager=self.llm_manager,
            config=self.config
        )
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer",
            input_key="question",
            max_token_limit=self.config.MAX_MEMORY_TOKEN_LIMIT
        )
        
        self._initialized = False
    
    def initialize(self, db_path: str = None, reset: bool = False):
        """
        Initialize the chatbot (load models, setup vector store)
        
        Args:
            db_path: Path to ChromaDB storage
            reset: Whether to reset the vector store
        """
        print("Initializing RAG Chatbot...")
        
        # Initialize vector store
        self.vector_store.initialize(db_path=db_path, reset=reset)
        
        # Load embedding model
        self.embedding_manager.load_model()
        
        # LLM will be lazy-loaded on first query
        print("✅ RAG Chatbot initialized (LLM will load on first query)")
        
        self._initialized = True
    
    def index_documents(self, documents: List, chunk_size: int = None,
                       chunk_overlap: int = None):
        """
        Index documents into vector store
        
        Args:
            documents: List of LangChain Document objects
            chunk_size: Override chunk size
            chunk_overlap: Override chunk overlap
        """
        if not self._initialized:
            raise RuntimeError("Chatbot not initialized. Call initialize() first.")
        
        from .document_processor import DocumentProcessor
        
        # Create processor with custom chunking if specified
        if chunk_size or chunk_overlap:
            custom_config = RAGConfig()
            if chunk_size:
                custom_config.CHUNK_SIZE = chunk_size
            if chunk_overlap:
                custom_config.CHUNK_OVERLAP = chunk_overlap
            processor = DocumentProcessor(config=custom_config)
        else:
            processor = DocumentProcessor(config=self.config)
        
        # Split documents into chunks
        text_chunks = processor.split_documents(documents)
        
        # Prepare for embedding
        texts, metadatas = processor.prepare_chunks_for_embedding(text_chunks)
        
        # Generate embeddings
        embeddings = self.embedding_manager.generate_embeddings(texts)
        
        # Add to vector store
        self.vector_store.add_documents(
            embeddings=embeddings.tolist(),
            texts=texts,
            metadatas=metadatas
        )
        
        print(f"✅ Indexed {len(texts)} chunks")
    
    def query(self, question: str, n_results: int = None,
             use_rewrite: bool = True, similarity_threshold: float = None,
             metadata_filter: Dict = None) -> Tuple[str, List[Dict]]:
        """
        Query the RAG system with a question
        
        Args:
            question: User question
            n_results: Number of documents to retrieve
            use_rewrite: Whether to rewrite follow-up questions
            similarity_threshold: Minimum similarity for retrieval
            metadata_filter: Optional filter for document metadata
            
        Returns:
            Tuple of (answer, sources)
        """
        if not self._initialized:
            raise RuntimeError("Chatbot not initialized. Call initialize() first.")
        
        # Get chat history
        chat_history = self.memory.load_memory_variables({}).get("chat_history", [])
        
        # Rewrite question if it's a follow-up
        retrieval_question = question
        if use_rewrite and len(chat_history) > 0:
            retrieval_question = self.retriever.rewrite_query(question, chat_history)
        
        # Retrieve relevant documents
        retrieved_docs, retrieved_metadata, similarities = self.retriever.retrieve(
            query=retrieval_question,
            n_results=n_results,
            similarity_threshold=similarity_threshold,
            metadata_filter=metadata_filter
        )
        
        # Check if any relevant documents found
        if not retrieved_docs:
            no_context_answer = "I cannot find relevant information in the provided documents to answer this question. Please ask something related to the document content."
            
            # Save to memory
            self.memory.save_context(
                {"question": question},
                {"answer": no_context_answer}
            )
            
            return no_context_answer, []
        
        # Format context from retrieved documents
        context = self.retriever.format_context(retrieved_docs, retrieved_metadata)
        
        # Prepare messages for LLM
        messages = [
            {
                "role": "system",
                "content": self.config.SYSTEM_PROMPT
            }
        ]
        
        # Add conversation history
        for msg in chat_history[-self.config.MAX_HISTORY_TURNS:]:
            if isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                messages.append({"role": "assistant", "content": msg.content})
        
        # Add current question with context
        messages.append({
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}"
        })
        
        # Generate answer
        print("⏳ Generating answer...")
        answer = self.llm_manager.generate(messages)
        
        # Save to memory
        self.memory.save_context(
            {"question": question},
            {"answer": answer}
        )
        
        # Prepare source information
        sources = self.retriever.prepare_sources(
            retrieved_docs,
            retrieved_metadata,
            similarities
        )
        
        return answer, sources
    
    def clear_memory(self):
        """Clear conversation history"""
        self.memory.clear()
        print("🗑️ Conversation history cleared")
    
    def get_conversation_history(self) -> List:
        """
        Get current conversation history
        
        Returns:
            List of messages
        """
        return self.memory.load_memory_variables({}).get("chat_history", [])
    
    def get_system_info(self) -> Dict:
        """
        Get system information
        
        Returns:
            Dictionary with system status
        """
        return {
            "initialized": self._initialized,
            "embedding_model": self.config.EMBEDDING_MODEL,
            "llm_model": self.config.LLM_MODEL,
            "llm_info": self.llm_manager.get_model_info(),
            "vector_store_count": self.vector_store.get_document_count(),
            "conversation_turns": len(self.get_conversation_history()) // 2
        }
