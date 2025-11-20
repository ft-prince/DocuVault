"""
Embedding generation module
Handles loading embedding models and generating embeddings
"""

import numpy as np
import torch
from typing import List
from sentence_transformers import SentenceTransformer

from .config import RAGConfig


class EmbeddingManager:
    """Manages embedding model and generates embeddings for text"""
    
    def __init__(self, config: RAGConfig = None):
        """
        Initialize embedding manager
        
        Args:
            config: RAGConfig instance. If None, uses default.
        """
        self.config = config or RAGConfig()
        self.model = None
        self.device = self._detect_device()
        self.config.set_device(self.device)
    
    def _detect_device(self) -> str:
        """
        Detect available device (CUDA or CPU)
        
        Returns:
            Device string ('cuda' or 'cpu')
        """
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Using device: {device}")
        return device
    
    def load_model(self):
        """Load the embedding model"""
        if self.model is not None:
            print("Embedding model already loaded")
            return
        
        print(f"Loading embedding model: {self.config.EMBEDDING_MODEL}")
        
        self.model = SentenceTransformer(
            self.config.EMBEDDING_MODEL,
            device=self.device,
            trust_remote_code=True
        )
        
        embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"✅ Embedding model loaded: {self.config.EMBEDDING_MODEL}")
        print(f"Embedding dimension: {embedding_dim}")
    
    def generate_embeddings(self, texts: List[str], show_progress: bool = True) -> np.ndarray:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings
            show_progress: Whether to show progress bar
            
        Returns:
            NumPy array of embeddings
        """
        if self.model is None:
            self.load_model()
        
        print(f"\nGenerating embeddings for {len(texts)} texts...")
        
        embeddings = self.model.encode(
            texts,
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
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        
        return embedding
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings
        
        Returns:
            Embedding dimension
        """
        if self.model is None:
            self.load_model()
        
        return self.model.get_sentence_embedding_dimension()
