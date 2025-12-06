"""
Enhanced Embedding Module with Multi-Modal Support
Handles text, tables, and structured content differently for better retrieval
"""

import numpy as np
import torch
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer

from .config import RAGConfig


class EnhancedEmbeddingManager:
    """
    Enhanced embedding manager with support for different content types
    """
    
    def __init__(self, config: RAGConfig = None):
        """
        Initialize enhanced embedding manager
        
        Args:
            config: RAGConfig instance
        """
        self.config = config or RAGConfig()
        self.model = None
        self.device = self._detect_device()
        self.config.set_device(self.device)
    
    def _detect_device(self) -> str:
        """Detect available device (CUDA or CPU)"""
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Using device: {device}")
        return device
    
    def load_model(self):
        """Load the embedding model"""
        if self.model is not None:
            print("Embedding model already loaded")
            return
        
        print(f"🔄 Loading embedding model: {self.config.EMBEDDING_MODEL}")
        
        self.model = SentenceTransformer(
            self.config.EMBEDDING_MODEL,
            device=self.device,
            trust_remote_code=True
        )
        
        embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"✅ Embedding model loaded: {self.config.EMBEDDING_MODEL}")
        print(f"   Dimension: {embedding_dim}")
    
    def preprocess_text_for_embedding(self, text: str, chunk_type: str = 'text') -> str:
        """
        Preprocess text based on content type for better embeddings
        
        Args:
            text: Input text
            chunk_type: Type of chunk ('text', 'table', 'image_desc')
            
        Returns:
            Preprocessed text
        """
        if chunk_type == 'table':
            # Add context to tables
            if '[TABLE]' in text:
                text = text.replace('[TABLE]', 'Data table: ')
                text = text.replace('[/TABLE]', '')
            
            # Normalize table formatting
            text = text.replace(' | ', ', ')
            
        elif chunk_type == 'image_desc':
            # Add context to image descriptions
            if '[IMAGE DESCRIPTION:' in text:
                text = text.replace('[IMAGE DESCRIPTION:', 'Visual content shows: ')
                text = text.replace(']', '')
        
        # General cleaning
        text = ' '.join(text.split())  # Normalize whitespace
        text = text.strip()
        
        return text
    
    def generate_embeddings_enhanced(self, texts: List[str], 
                                    chunk_types: Optional[List[str]] = None,
                                    show_progress: bool = True) -> np.ndarray:
        """
        Generate embeddings with preprocessing based on content type
        
        Args:
            texts: List of text strings
            chunk_types: Optional list of chunk types for each text
            show_progress: Whether to show progress bar
            
        Returns:
            NumPy array of embeddings
        """
        if self.model is None:
            self.load_model()
        
        # Preprocess texts if chunk types provided
        if chunk_types:
            processed_texts = [
                self.preprocess_text_for_embedding(text, chunk_type)
                for text, chunk_type in zip(texts, chunk_types)
            ]
        else:
            processed_texts = texts
        
        print(f"\n🔄 Generating embeddings for {len(texts)} chunks...")
        
        embeddings = self.model.encode(
            processed_texts,
            show_progress_bar=show_progress,
            batch_size=self.config.EMBEDDING_BATCH_SIZE,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        
        print(f"✅ Embeddings generated! Shape: {embeddings.shape}")
        return embeddings
    
    def generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Generate embedding for a single query
        
        Args:
            query: Query text string
            
        Returns:
            NumPy array of embedding
        """
        if self.model is None:
            self.load_model()
        
        embedding = self.model.encode(
            query,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        
        return embedding
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        if self.model is None:
            self.load_model()
        
        return self.model.get_sentence_embedding_dimension()
    
    # Backward compatibility methods
    def generate_embeddings(self, texts: List[str], show_progress: bool = True) -> np.ndarray:
        """Original method for backward compatibility"""
        return self.generate_embeddings_enhanced(texts, show_progress=show_progress)