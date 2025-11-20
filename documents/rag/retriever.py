"""
Retriever module for query processing and document retrieval
"""

from typing import List, Dict, Tuple

from .config import RAGConfig
from .embeddings import EmbeddingManager
from .vector_store import VectorStore
from .llm_manager import LLMManager


class Retriever:
    """Handles query rewriting and document retrieval"""
    
    def __init__(self, embedding_manager: EmbeddingManager,
                 vector_store: VectorStore,
                 llm_manager: LLMManager = None,
                 config: RAGConfig = None):
        """
        Initialize retriever
        
        Args:
            embedding_manager: EmbeddingManager instance
            vector_store: VectorStore instance
            llm_manager: LLMManager instance (optional, for query rewriting)
            config: RAGConfig instance
        """
        self.embedding_manager = embedding_manager
        self.vector_store = vector_store
        self.llm_manager = llm_manager
        self.config = config or RAGConfig()
    
    def retrieve(self, query: str, n_results: int = None,
                similarity_threshold: float = None,
                metadata_filter: Dict = None) -> Tuple[List[str], List[Dict], List[float]]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Query text
            n_results: Number of results to retrieve
            similarity_threshold: Minimum similarity score
            metadata_filter: Optional metadata filter for ChromaDB
            
        Returns:
            Tuple of (documents, metadatas, similarity_scores)
        """
        # Generate query embedding
        query_embedding = self.embedding_manager.generate_query_embedding(query)
        
        # Query vector store
        results = self.vector_store.query(
            query_embedding=query_embedding,
            n_results=n_results or self.config.N_RESULTS,
            where=metadata_filter
        )
        
        # Filter by similarity threshold
        filtered_docs, filtered_metadata, filtered_similarities = \
            self.vector_store.filter_by_similarity(
                results,
                threshold=similarity_threshold or self.config.SIMILARITY_THRESHOLD
            )
        
        return filtered_docs, filtered_metadata, filtered_similarities
    
    def rewrite_query(self, query: str, chat_history: List) -> str:
        """
        Rewrite follow-up query to be standalone
        
        Args:
            query: Current query
            chat_history: Conversation history
            
        Returns:
            Rewritten query or original if no LLM available
        """
        if self.llm_manager is None:
            return query
        
        if not chat_history or len(chat_history) == 0:
            return query
        
        return self.llm_manager.rewrite_question(query, chat_history)
    
    def format_context(self, documents: List[str], metadatas: List[Dict]) -> str:
        """
        Format retrieved documents into context string
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for doc, meta in zip(documents, metadatas):
            source = meta.get('source', 'Unknown')
            page = meta.get('page', 0) + 1
            context_parts.append(f"[Source: {source}, Page {page}]\n{doc}")
        
        return "\n\n".join(context_parts)
    
    def prepare_sources(self, documents: List[str], metadatas: List[Dict],
                       similarities: List[float]) -> List[Dict]:
        """
        Prepare source information for response
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries
            similarities: List of similarity scores
            
        Returns:
            List of source dictionaries
        """
        sources = []
        
        for doc, meta, sim in zip(documents, metadatas, similarities):
            sources.append({
                'source': meta.get('source', 'Unknown'),
                'page': meta.get('page', 0) + 1,
                'similarity': sim,
                'text_preview': doc[:100]
            })
        
        return sources
