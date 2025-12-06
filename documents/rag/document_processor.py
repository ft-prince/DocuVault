"""
Enhanced Document Processing Module for RAG System
Supports: PDF text, tables (pdfplumber/Camelot), OCR (Tesseract), and image understanding (BLIP-2)
"""

import os
import io
import base64
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# PDF Processing
import pdfplumber
import fitz  # PyMuPDF for fallback
from pdf2image import convert_from_path
import camelot  # For complex table extraction

# OCR
from PIL import Image
import pytesseract

# Image Understanding
import torch
from transformers import Blip2Processor, Blip2ForConditionalGeneration

# LangChain
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import RAGConfig


class EnhancedDocumentProcessor:
    """
    Advanced document processor with multi-modal capabilities:
    - Text extraction with pdfplumber
    - Table extraction with Camelot/pdfplumber
    - OCR for scanned pages with Tesseract
    - Image understanding with BLIP-2
    """
    
    def __init__(self, config: RAGConfig = None):
        """
        Initialize enhanced document processor
        
        Args:
            config: RAGConfig instance
        """
        self.config = config or RAGConfig()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP,
            length_function=len,
            separators=self.config.TEXT_SEPARATORS
        )
        
        # Image understanding model (lazy loaded)
        self.blip_processor = None
        self.blip_model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Processing statistics
        self.stats = {
            'total_pages': 0,
            'text_pages': 0,
            'ocr_pages': 0,
            'tables_extracted': 0,
            'images_processed': 0
        }
    
    def load_image_model(self):
        """Lazy load BLIP-2 model for image understanding"""
        if self.blip_model is None:
            print("🔄 Loading BLIP-2 model for image understanding...")
            
            model_name = "Salesforce/blip2-opt-2.7b"  # Smaller model for efficiency
            
            self.blip_processor = Blip2Processor.from_pretrained(model_name)
            self.blip_model = Blip2ForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                device_map="auto"
            )
            
            print(f"✅ BLIP-2 model loaded on {self.device}")
    
    def is_page_scanned(self, page) -> bool:
        """
        Detect if a page is scanned/image-based
        
        Args:
            page: pdfplumber page object
            
        Returns:
            True if page appears to be scanned
        """
        text = page.extract_text()
        
        # If very little text but has images, likely scanned
        if not text or len(text.strip()) < 50:
            if len(page.images) > 0:
                return True
        
        # Check text-to-image ratio
        if text and len(page.images) > 0:
            text_len = len(text.strip())
            page_area = page.width * page.height
            
            # If very little text relative to page size, might be scanned
            if text_len < 100 and page_area > 100000:
                return True
        
        return False
    
    def extract_text_with_pdfplumber(self, pdf_path: str) -> List[Dict]:
        """
        Extract text from PDF using pdfplumber (better than PyMuPDF for text)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of page dictionaries with text and metadata
        """
        pages_data = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Try regular text extraction
                text = page.extract_text()
                
                # Check if page needs OCR
                needs_ocr = self.is_page_scanned(page)
                
                if needs_ocr or not text or len(text.strip()) < 20:
                    print(f"   Page {page_num}: Applying OCR (scanned/low text)")
                    text = self.ocr_page(pdf_path, page_num)
                    self.stats['ocr_pages'] += 1
                else:
                    self.stats['text_pages'] += 1
                
                pages_data.append({
                    'page_number': page_num,
                    'text': text.strip(),
                    'needs_ocr': needs_ocr,
                    'char_count': len(text),
                    'word_count': len(text.split()),
                    'has_images': len(page.images) > 0,
                    'image_count': len(page.images)
                })
                
                self.stats['total_pages'] += 1
        
        return pages_data
    
    def ocr_page(self, pdf_path: str, page_num: int) -> str:
        """
        Perform OCR on a specific page using Tesseract
        
        Args:
            pdf_path: Path to PDF file
            page_num: Page number (0-indexed)
            
        Returns:
            Extracted text
        """
        try:
            # Convert PDF page to image
            images = convert_from_path(
                pdf_path,
                first_page=page_num + 1,
                last_page=page_num + 1,
                dpi=300  # High DPI for better OCR
            )
            
            if not images:
                return ""
            
            # Perform OCR
            text = pytesseract.image_to_string(
                images[0],
                lang='eng',
                config='--psm 1'  # Automatic page segmentation with OSD
            )
            
            return text.strip()
            
        except Exception as e:
            print(f"      OCR failed for page {page_num}: {e}")
            return ""
    
    def extract_tables_camelot(self, pdf_path: str, page_num: int) -> List[str]:
        """
        Extract tables using Camelot (better for complex tables)
        
        Args:
            pdf_path: Path to PDF
            page_num: Page number (1-indexed for Camelot)
            
        Returns:
            List of table strings in markdown format
        """
        try:
            # Camelot uses 1-based indexing
            tables = camelot.read_pdf(
                pdf_path,
                pages=str(page_num + 1),
                flavor='lattice',  # For tables with lines
                suppress_stdout=True
            )
            
            table_texts = []
            for table in tables:
                # Convert to markdown format
                df = table.df
                markdown_table = df.to_markdown(index=False)
                table_texts.append(markdown_table)
                self.stats['tables_extracted'] += 1
            
            return table_texts
            
        except Exception as e:
            # Fallback to pdfplumber for tables
            return []
    
    def extract_tables_pdfplumber(self, page) -> List[str]:
        """
        Extract tables using pdfplumber (fallback method)
        
        Args:
            page: pdfplumber page object
            
        Returns:
            List of table strings
        """
        try:
            tables = page.extract_tables()
            
            if not tables:
                return []
            
            table_texts = []
            for table in tables:
                # Convert to markdown-like format
                if not table or len(table) == 0:
                    continue
                
                # Format as text table
                table_str = "\n".join([" | ".join([str(cell) if cell else "" for cell in row]) for row in table])
                table_texts.append(f"\n[TABLE]\n{table_str}\n[/TABLE]\n")
                self.stats['tables_extracted'] += 1
            
            return table_texts
            
        except Exception as e:
            return []
    
    def extract_images_and_describe(self, pdf_path: str, page_num: int) -> List[Dict]:
        """
        Extract images from page and generate descriptions using BLIP-2
        
        Args:
            pdf_path: Path to PDF
            page_num: Page number
            
        Returns:
            List of image descriptions
        """
        image_descriptions = []
        
        try:
            # Convert page to image
            images = convert_from_path(
                pdf_path,
                first_page=page_num + 1,
                last_page=page_num + 1,
                dpi=150
            )
            
            if not images:
                return []
            
            page_image = images[0]
            
            # Load BLIP-2 model if not loaded
            self.load_image_model()
            
            # Process with BLIP-2
            inputs = self.blip_processor(page_image, return_tensors="pt").to(self.device)
            
            # Generate caption
            generated_ids = self.blip_model.generate(**inputs, max_new_tokens=50)
            caption = self.blip_processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
            
            # Generate detailed description with prompt
            prompt = "Question: What is shown in this image? Describe the key elements. Answer:"
            inputs = self.blip_processor(page_image, text=prompt, return_tensors="pt").to(self.device)
            
            generated_ids = self.blip_model.generate(**inputs, max_new_tokens=100)
            description = self.blip_processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
            
            image_descriptions.append({
                'caption': caption,
                'description': description,
                'page': page_num
            })
            
            self.stats['images_processed'] += 1
            
        except Exception as e:
            print(f"      Image processing failed for page {page_num}: {e}")
        
        return image_descriptions
    
    def process_pdf_enhanced(self, pdf_path: str, source_name: str,
                            extract_tables: bool = True,
                            describe_images: bool = True) -> List[Dict]:
        """
        Enhanced PDF processing with all features
        
        Args:
            pdf_path: Path to PDF file
            source_name: Document identifier
            extract_tables: Whether to extract tables
            describe_images: Whether to describe images with BLIP-2
            
        Returns:
            List of page dictionaries with enhanced content
        """
        print(f"\n📄 Processing: {source_name}")
        
        # Reset stats
        self.stats = {k: 0 for k in self.stats}
        
        enhanced_pages = []
        
        # Extract text with pdfplumber
        pages_data = self.extract_text_with_pdfplumber(pdf_path)
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page_data in enumerate(pages_data):
                page = pdf.pages[page_idx]
                page_content = page_data['text']
                
                # Extract tables if enabled
                if extract_tables:
                    # Try Camelot first
                    tables = self.extract_tables_camelot(pdf_path, page_idx)
                    
                    # Fallback to pdfplumber
                    if not tables:
                        tables = self.extract_tables_pdfplumber(page)
                    
                    if tables:
                        page_content += "\n\n" + "\n\n".join(tables)
                
                # Describe images if enabled and page has images
                if describe_images and page_data['has_images']:
                    image_descriptions = self.extract_images_and_describe(pdf_path, page_idx)
                    
                    for img_desc in image_descriptions:
                        page_content += f"\n\n[IMAGE DESCRIPTION: {img_desc['description']}]"
                
                enhanced_pages.append({
                    'page_number': page_idx,
                    'source': source_name,
                    'text': page_content,
                    'char_count': len(page_content),
                    'word_count': len(page_content.split()),
                    'needs_ocr': page_data['needs_ocr'],
                    'has_tables': extract_tables and len(self.extract_tables_pdfplumber(page)) > 0,
                    'has_images': page_data['has_images']
                })
        
        # Print statistics
        print(f"✅ Processed {self.stats['total_pages']} pages")
        print(f"   📝 Text pages: {self.stats['text_pages']}")
        print(f"   🔍 OCR pages: {self.stats['ocr_pages']}")
        print(f"   📊 Tables extracted: {self.stats['tables_extracted']}")
        print(f"   🖼️  Images processed: {self.stats['images_processed']}")
        
        return enhanced_pages
    
    def convert_to_langchain_documents(self, enhanced_pages: List[Dict]) -> List[Document]:
        """
        Convert enhanced page data to LangChain Document objects
        
        Args:
            enhanced_pages: List of enhanced page dictionaries
            
        Returns:
            List of LangChain Documents
        """
        documents = []
        
        for page_data in enhanced_pages:
            doc = Document(
                page_content=page_data['text'],
                metadata={
                    'source': page_data['source'],
                    'page': page_data['page_number'],
                    'page_number': page_data['page_number'],
                    'needs_ocr': page_data.get('needs_ocr', False),
                    'has_tables': page_data.get('has_tables', False),
                    'has_images': page_data.get('has_images', False)
                }
            )
            documents.append(doc)
        
        return documents
    
    def split_documents_smart(self, documents: List[Document]) -> List[Document]:
        """
        Smart document splitting that preserves tables and important structures
        
        Args:
            documents: List of LangChain Documents
            
        Returns:
            List of chunked Documents
        """
        chunks = []
        
        for doc in documents:
            text = doc.page_content
            
            # Check if document has tables
            has_table = '[TABLE]' in text
            
            if has_table:
                # Split around tables to keep them intact
                parts = text.split('[TABLE]')
                
                for i, part in enumerate(parts):
                    if '[/TABLE]' in part:
                        # This is a table, keep it whole
                        table_content = '[TABLE]' + part
                        chunks.append(Document(
                            page_content=table_content,
                            metadata={**doc.metadata, 'chunk_type': 'table', 'chunk_index': i}
                        ))
                    else:
                        # Regular text, split normally
                        text_chunks = self.text_splitter.split_text(part)
                        for j, chunk_text in enumerate(text_chunks):
                            chunks.append(Document(
                                page_content=chunk_text,
                                metadata={**doc.metadata, 'chunk_type': 'text', 'chunk_index': f"{i}_{j}"}
                            ))
            else:
                # No tables, split normally
                text_chunks = self.text_splitter.split_documents([doc])
                for i, chunk in enumerate(text_chunks):
                    chunk.metadata['chunk_type'] = 'text'
                    chunk.metadata['chunk_index'] = i
                    chunks.append(chunk)
        
        print(f"📦 Created {len(chunks)} smart chunks from {len(documents)} pages")
        
        return chunks
    
    def process_document_complete(self, pdf_path: str, 
                                  extract_tables: bool = True,
                                  describe_images: bool = False) -> List[Document]:
        """
        Complete document processing pipeline
        
        Args:
            pdf_path: Path to PDF file
            extract_tables: Whether to extract tables
            describe_images: Whether to describe images (resource intensive)
            
        Returns:
            List of chunked LangChain Documents ready for embedding
        """
        source_name = Path(pdf_path).name
        
        # Step 1: Enhanced extraction
        enhanced_pages = self.process_pdf_enhanced(
            pdf_path,
            source_name,
            extract_tables=extract_tables,
            describe_images=describe_images
        )
        
        # Step 2: Convert to LangChain documents
        documents = self.convert_to_langchain_documents(enhanced_pages)
        
        # Step 3: Smart chunking
        chunks = self.split_documents_smart(documents)
        
        return chunks
    
    def get_processing_stats(self) -> Dict:
        """Get processing statistics"""
        return self.stats.copy()