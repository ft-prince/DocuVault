"""
Enhanced Retriever Module with Hybrid Search and Better Context Formatting
"""

from typing import List, Dict, Tuple, Optional
import re

from .config import RAGConfig
from .embeddings import EnhancedEmbeddingManager
from .vector_store import VectorStore
from .llm_manager import LLMManager


class EnhancedRetriever:
    """
    Enhanced retriever with:
    - Better context formatting for tables and structured content
    - Hybrid search combining semantic + keyword matching
    - Improved query rewriting
    - Relevance re-ranking
    """
    
    def __init__(self, embedding_manager: EnhancedEmbeddingManager,
                 vector_store: VectorStore,
                 llm_manager: LLMManager = None,
                 config: RAGConfig = None):
        """
        Initialize enhanced retriever
        
        Args:
            embedding_manager: Enhanced embedding manager
            vector_store: Vector store instance
            llm_manager: LLM manager for query rewriting
            config: RAG configuration
        """
        self.embedding_manager = embedding_manager
        self.vector_store = vector_store
        self.llm_manager = llm_manager
        self.config = config or RAGConfig()
    
    def extract_keywords(self, query: str) -> List[str]:
        """
        Extract important keywords from query for hybrid search
        
        Args:
            query: Query text
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction (can be enhanced with NLP)
        words = query.lower().split()
        
        # Remove common words
        stop_words = {'what', 'when', 'where', 'who', 'how', 'why', 'is', 'are', 'the', 'a', 'an', 'in', 'on', 'at'}
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        
        return keywords
    
    def keyword_match_score(self, text: str, keywords: List[str]) -> float:
        """
        Calculate keyword match score for text
        
        Args:
            text: Document text
            keywords: List of keywords to match
            
        Returns:
            Match score (0-1)
        """
        if not keywords:
            return 0.0
        
        text_lower = text.lower()
        matches = sum(1 for kw in keywords if kw in text_lower)
        
        return matches / len(keywords)
    
    def retrieve_hybrid(self, query: str, n_results: int = 6,
                       metadata_filter: Dict = None,
                       semantic_weight: float = 0.7) -> Tuple[List[str], List[Dict], List[float]]:
        """
        Hybrid retrieval combining semantic and keyword matching
        
        Args:
            query: Query text
            n_results: Number of results to retrieve
            metadata_filter: Optional metadata filter
            semantic_weight: Weight for semantic similarity (vs keyword matching)
            
        Returns:
            Tuple of (documents, metadatas, combined_scores)
        """
        # Get more results initially for re-ranking
        retrieve_n = n_results * 2
        
        # Semantic search
        query_embedding = self.embedding_manager.generate_query_embedding(query)
        
        results = self.vector_store.query(
            query_embedding=query_embedding,
            n_results=retrieve_n,
            where=metadata_filter
        )
        
        docs, metadatas, semantic_scores = self.vector_store.process_results(results)
        
        if not docs:
            return [], [], []
        
        # Keyword matching
        keywords = self.extract_keywords(query)
        keyword_scores = [self.keyword_match_score(doc, keywords) for doc in docs]
        
        # Combine scores
        combined_scores = [
            semantic_weight * sem_score + (1 - semantic_weight) * kw_score
            for sem_score, kw_score in zip(semantic_scores, keyword_scores)
        ]
        
        # Sort by combined score and take top N
        sorted_indices = sorted(range(len(combined_scores)), 
                              key=lambda i: combined_scores[i], 
                              reverse=True)[:n_results]
        
        final_docs = [docs[i] for i in sorted_indices]
        final_metadatas = [metadatas[i] for i in sorted_indices]
        final_scores = [combined_scores[i] for i in sorted_indices]
        
        print(f"🔍 Hybrid search: Retrieved {len(final_docs)} chunks")
        print(f"   Keywords: {keywords}")
        print(f"   Top scores: {[f'{s:.3f}' for s in final_scores[:3]]}")
        
        return final_docs, final_metadatas, final_scores
    
    def retrieve(self, query: str, n_results: int = 4,
                metadata_filter: Dict = None,
                use_hybrid: bool = True) -> Tuple[List[str], List[Dict], List[float]]:
        """
        Retrieve relevant documents (with optional hybrid search)
        
        Args:
            query: Query text
            n_results: Number of results
            metadata_filter: Optional metadata filter
            use_hybrid: Whether to use hybrid search
            
        Returns:
            Tuple of (documents, metadatas, scores)
        """
        if use_hybrid:
            return self.retrieve_hybrid(query, n_results, metadata_filter)
        else:
            # Standard semantic search
            query_embedding = self.embedding_manager.generate_query_embedding(query)
            
            results = self.vector_store.query(
                query_embedding=query_embedding,
                n_results=n_results,
                where=metadata_filter
            )
            
            return self.vector_store.process_results(results)
    
    def format_context_enhanced(self, documents: List[str], metadatas: List[Dict]) -> str:
        """
        Enhanced context formatting that handles tables and structured content better
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for idx, (doc, meta) in enumerate(zip(documents, metadatas), 1):
            source = meta.get('source', 'Unknown')
            page = meta.get('page', 0) + 1
            chunk_type = meta.get('chunk_type', 'text')
            
            # Format based on content type
            if '[TABLE]' in doc:
                # Table formatting
                table_content = doc.replace('[TABLE]', '').replace('[/TABLE]', '').strip()
                formatted = f"""
From {source} (page {page}) - Table:
{table_content}
"""
            elif '[IMAGE DESCRIPTION:' in doc:
                # Image description formatting
                img_content = doc.replace('[IMAGE DESCRIPTION:', '').replace(']', '').strip()
                formatted = f"""
From {source} (page {page}) - Image showing:
{img_content}
"""
            else:
                # Regular text formatting
                formatted = f"""
From {source} (page {page}):
{doc}
"""
            
            context_parts.append(formatted.strip())
        
        return "\n\n" + "\n\n".join(context_parts) + "\n"
    
    def rewrite_query(self, query: str, chat_history: List) -> str:
        """
        Enhanced query rewriting with better understanding
        
        Args:
            query: Current query
            chat_history: Conversation history
            
        Returns:
            Rewritten query
        """
        if self.llm_manager is None:
            return query
        
        if not chat_history or len(chat_history) == 0:
            return query
        
        # Check if query is actually a follow-up
        follow_up_indicators = ['it', 'this', 'that', 'these', 'those', 'they', 'them']
        is_followup = any(indicator in query.lower().split()[:3] for indicator in follow_up_indicators)
        
        if not is_followup and len(query.split()) > 5:
            # Query seems standalone already
            return query
        
        return self.llm_manager.rewrite_question(query, chat_history)
    
    def prepare_sources_enhanced(self, documents: List[str], metadatas: List[Dict],
                                similarities: List[float]) -> List[Dict]:
        """
        Enhanced source preparation with better metadata
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries
            similarities: List of similarity scores
            
        Returns:
            List of enhanced source dictionaries
        """
        sources = []
        
        for doc, meta, sim in zip(documents, metadatas, similarities):
            # Determine content type
            if '[TABLE]' in doc:
                content_type = 'table'
                preview = doc.replace('[TABLE]', '').replace('[/TABLE]', '')[:150]
            elif '[IMAGE DESCRIPTION:' in doc:
                content_type = 'image'
                preview = doc.replace('[IMAGE DESCRIPTION:', '').replace(']', '')[:150]
            else:
                content_type = 'text'
                preview = doc[:150]
            
            sources.append({
                'source': meta.get('source', 'Unknown'),
                'page': meta.get('page', 0) + 1,
                'similarity': round(sim, 3),
                'content_type': content_type,
                'text_preview': preview.strip() + '...',
                'needs_ocr': meta.get('needs_ocr', False),
                'has_tables': meta.get('has_tables', False),
                'has_images': meta.get('has_images', False)
            })
        
        return sources
    
    # Backward compatibility
    def format_context(self, documents: List[str], metadatas: List[Dict]) -> str:
        """Backward compatible method"""
        return self.format_context_enhanced(documents, metadatas)
    
    def prepare_sources(self, documents: List[str], metadatas: List[Dict],
                       similarities: List[float]) -> List[Dict]:
        """Backward compatible method"""
        return self.prepare_sources_enhanced(documents, metadatas, similarities)