"""
Document processing module for RAG system
Handles PDF loading, text extraction, and chunking
"""

import fitz  # PyMuPDF
from typing import List, Dict
from tqdm.auto import tqdm
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader

from .config import RAGConfig


class DocumentProcessor:
    """Handles document loading, text extraction, and chunking"""
    
    def __init__(self, config: RAGConfig = None):
        """
        Initialize document processor
        
        Args:
            config: RAGConfig instance. If None, uses default.
        """
        self.config = config or RAGConfig()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP,
            length_function=len,
            separators=self.config.TEXT_SEPARATORS
        )
    
    @staticmethod
    def text_formatter(text: str) -> str:
        """
        Performs minor formatting on text
        
        Args:
            text: Raw text string
            
        Returns:
            Cleaned text
        """
        cleaned_text = text.replace("\n", " ").strip()
        return cleaned_text
    
    def open_and_read_pdf(self, pdf_path: str, source_name: str) -> List[Dict]:
        """
        Opens a PDF file, reads its text content page by page
        
        Args:
            pdf_path: Path to PDF file
            source_name: Name identifier for the source document
            
        Returns:
            List of dictionaries containing page information and text
        """
        doc = fitz.open(pdf_path)
        pages_and_texts = []
        
        for page_number, page in tqdm(enumerate(doc), desc=f"Reading {source_name}"):
            text = page.get_text()
            text = self.text_formatter(text)
            
            pages_and_texts.append({
                "page_number": page_number,
                "source": source_name,
                "page_char_count": len(text),
                "page_word_count": len(text.split(" ")),
                "page_sentence_count_raw": len(text.split(". ")),
                "page_token_count": len(text) / 4,
                "text": text
            })
        
        doc.close()
        return pages_and_texts
    
    def load_documents_from_directory(self, pdf_dir: str) -> List[Document]:
        """
        Load all PDF documents from a directory using LangChain's DirectoryLoader
        
        Args:
            pdf_dir: Path to directory containing PDF files
            
        Returns:
            List of LangChain Document objects
        """
        loader = DirectoryLoader(
            pdf_dir,
            glob="*.pdf",
            loader_cls=PyPDFLoader,
            show_progress=True,
            use_multithreading=True,
            max_concurrency=4
        )
        
        documents = loader.load()
        print(f"✅ Loaded {len(documents)} document pages")
        
        return documents
    
    def load_single_document(self, pdf_path: str) -> List[Document]:
        """
        Load a single PDF document
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of LangChain Document objects (one per page)
        """
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        print(f"✅ Loaded {len(documents)} pages from {pdf_path}")
        
        return documents
    
    def process_documents(self, documents: List[Document]) -> List[Dict]:
        """
        Process raw documents into structured format with metadata
        
        Args:
            documents: List of LangChain Document objects
            
        Returns:
            List of dictionaries with page information
        """
        all_pages_and_texts = []
        
        for doc in documents:
            source_name = doc.metadata.get('source', 'Unknown').split('/')[-1]
            page_number = doc.metadata.get('page', 0)
            text = self.text_formatter(doc.page_content)
            
            all_pages_and_texts.append({
                "page_number": page_number,
                "source": source_name,
                "page_char_count": len(text),
                "page_word_count": len(text.split(" ")),
                "page_sentence_count_raw": len(text.split(". ")),
                "page_token_count": len(text) / 4,
                "text": text
            })
        
        return all_pages_and_texts
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks for embedding
        
        Args:
            documents: List of LangChain Document objects
            
        Returns:
            List of chunked Document objects
        """
        text_chunks = self.text_splitter.split_documents(documents)
        chunk_lengths = [len(chunk.page_content) for chunk in text_chunks]
        
        print(f"Created {len(text_chunks)} chunks from {len(documents)} documents")
        print(f"Chunk statistics:")
        print(f" - Min: {min(chunk_lengths) if chunk_lengths else 0} chars")
        print(f" - Max: {max(chunk_lengths) if chunk_lengths else 0} chars")
        print(f" - Avg: {sum(chunk_lengths)/len(chunk_lengths) if chunk_lengths else 0:.0f} chars")
        
        return text_chunks
    
    def prepare_chunks_for_embedding(self, text_chunks: List[Document]) -> tuple[List[str], List[Dict]]:
        """
        Prepare chunks for embedding by extracting text and metadata
        
        Args:
            text_chunks: List of Document chunks
            
        Returns:
            Tuple of (texts, metadatas)
        """
        texts = [chunk.page_content for chunk in text_chunks]
        metadatas = [
            {
                "page_number": chunk.metadata.get("page_number", 0),
                "source": chunk.metadata.get("source", "Unknown"),
                "page": chunk.metadata.get("page", 0)
            }
            for chunk in text_chunks
        ]
        
        return texts, metadatas
