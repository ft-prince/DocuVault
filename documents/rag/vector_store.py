"""
Vector store management using ChromaDB
Handles storage, retrieval, and similarity search
"""

import chromadb
from typing import List, Dict, Tuple
from chromadb.config import Settings

from .config import RAGConfig


class VectorStore:
    """Manages vector database operations using ChromaDB"""
    
    def __init__(self, config: RAGConfig = None):
        """
        Initialize vector store
        
        Args:
            config: RAGConfig instance. If None, uses default.
        """
        self.config = config or RAGConfig()
        self.client = None
        self.collection = None
    
    def initialize(self, db_path: str = None, reset: bool = False):
        """
        Initialize ChromaDB client and collection
        
        Args:
            db_path: Path to store ChromaDB data. If None, uses config path.
            reset: If True, deletes existing collection and creates new one
        """
        if db_path:
            self.config.set_chroma_path(db_path)
        elif not self.config.CHROMA_DB_PATH:
            raise ValueError("ChromaDB path must be set either in config or as parameter")
        
        print(f"Initializing ChromaDB at: {self.config.CHROMA_DB_PATH}")
        
        self.client = chromadb.PersistentClient(path=self.config.CHROMA_DB_PATH)
        
        # Delete collection if reset is True
        if reset:
            try:
                self.client.delete_collection(name=self.config.COLLECTION_NAME)
                print(f"Deleted existing collection: {self.config.COLLECTION_NAME}")
            except Exception as e:
                print(f"No existing collection to delete: {e}")
        
        # Create or get collection
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.config.COLLECTION_NAME,
                metadata={"description": "DocuVault document embeddings"}
            )
            print(f"✅ Collection '{self.config.COLLECTION_NAME}' ready")
        except Exception as e:
            print(f"Error creating collection: {e}")
            raise
    
    def add_documents(self, embeddings: List[List[float]], texts: List[str], 
                     metadatas: List[Dict], ids: List[str] = None):
        """
        Add documents to the vector store
        
        Args:
            embeddings: List of embedding vectors
            texts: List of text content
            metadatas: List of metadata dictionaries
            ids: List of unique IDs. If None, generates automatically.
        """
        if self.collection is None:
            raise RuntimeError("Collection not initialized. Call initialize() first.")
        
        if ids is None:
            ids = [f"chunk_{i}" for i in range(len(texts))]
        
        print(f"Adding {len(texts)} documents to vector store...")
        
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"✅ Added {self.collection.count()} total chunks to vector store")
    
    def query(self, query_embedding: List[float], n_results: int = None, 
             where: Dict = None) -> Dict:
        """
        Query the vector store for similar documents
        
        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return. If None, uses config default.
            where: Optional metadata filter
            
        Returns:
            Dictionary with 'documents', 'metadatas', 'distances', 'ids'
        """
        if self.collection is None:
            raise RuntimeError("Collection not initialized. Call initialize() first.")
        
        if n_results is None:
            n_results = self.config.N_RESULTS
        
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist() if hasattr(query_embedding, 'tolist') else query_embedding],
            n_results=n_results,
            include=['documents', 'metadatas', 'distances'],
            where=where
        )
        
        return results
    
    def delete_documents(self, ids: List[str]):
        """
        Delete documents from vector store by IDs
        
        Args:
            ids: List of document IDs to delete
        """
        if self.collection is None:
            raise RuntimeError("Collection not initialized. Call initialize() first.")
        
        self.collection.delete(ids=ids)
        print(f"Deleted {len(ids)} documents from vector store")
    
    def get_document_count(self) -> int:
        """
        Get total number of documents in collection
        
        Returns:
            Document count
        """
        if self.collection is None:
            return 0
        
        return self.collection.count()
    
    def process_results(self, results: Dict) -> Tuple[List, List, List]:
        """
        Process query results from vector store
        
        Args:
            results: Query results from vector store
            
        Returns:
            Tuple of (docs, metadata, similarities)
        """
        if not results['documents'] or not results['documents'][0]:
            return [], [], []
            
        retrieved_docs = results['documents'][0]
        retrieved_metadata = results['metadatas'][0]
        distances = results['distances'][0]
        
        # Convert distances to similarities
        similarities = [1 - dist for dist in distances]
        
        print(f"DEBUG: Top {len(similarities)} raw similarities: {[round(s, 3) for s in similarities]}")
        
        return retrieved_docs, retrieved_metadata, similarities
    
    def reset_collection(self):
        """Delete and recreate the collection"""
        if self.client:
            try:
                self.client.delete_collection(name=self.config.COLLECTION_NAME)
                print(f"Deleted collection: {self.config.COLLECTION_NAME}")
            except Exception as e:
                print(f"Error deleting collection: {e}")
            
            self.collection = self.client.create_collection(
                name=self.config.COLLECTION_NAME,
                metadata={"description": "DocuVault document embeddings"}
            )
            print(f"✅ Collection recreated: {self.config.COLLECTION_NAME}")
