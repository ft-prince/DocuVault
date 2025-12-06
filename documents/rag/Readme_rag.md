# Enhanced Multi-Modal RAG System

## 🎯 Overview

This is a significantly improved RAG (Retrieval-Augmented Generation) system with **multi-modal document understanding** capabilities. It goes beyond basic text extraction to understand tables, handle scanned documents via OCR, and optionally describe images.

### Key Improvements Over Original System

| Feature | Original System | Enhanced System |
|---------|----------------|-----------------|
| **Text Extraction** | PyMuPDF only | pdfplumber (better) + PyMuPDF fallback |
| **Table Handling** | ❌ Lost in text | ✅ Extracted and formatted (pdfplumber/Camelot) |
| **Scanned PDFs** | ❌ Poor results | ✅ OCR with Tesseract |
| **Images** | ❌ Ignored | ✅ Optional BLIP-2 descriptions |
| **Search Method** | Semantic only | Hybrid (semantic + keyword) |
| **Context Formatting** | Basic | Smart formatting by content type |
| **Chunk Strategy** | Fixed size | Smart splitting (preserves tables) |
| **Query Understanding** | Basic | Enhanced rewriting for follow-ups |

## 🚀 Quick Start

### 1. Installation

```bash
# Install Python dependencies
pip install -r requirements_enhanced.txt

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install tesseract-ocr poppler-utils ghostscript python3-tk

# For MacOS
brew install tesseract poppler ghostscript tcl-tk
```

### 2. Basic Usage

```python
from enhanced_conversation import RAGChatbot
from enhanced_config import RAGConfig

# Configure
config = RAGConfig()
config.set_chroma_path('./my_vector_store')

# Initialize
chatbot = RAGChatbot(config=config)
chatbot.initialize()

# Index a document
chatbot.index_documents(pdf_path='my_document.pdf')

# Query
answer, sources = chatbot.query("What does the revenue table show?")
print(answer)
```

### 3. Run Test Script

```bash
python test_enhanced_rag.py
```

## 📦 Architecture

```
enhanced_rag/
├── enhanced_config.py              # Configuration with multi-modal settings
├── enhanced_document_processor.py  # PDF processing with OCR & tables
├── enhanced_embeddings.py          # Embedding generation with preprocessing
├── enhanced_retriever.py           # Hybrid search & smart context formatting
├── enhanced_conversation.py        # Main chatbot interface
├── vector_store.py                 # ChromaDB integration (unchanged)
├── llm_manager.py                  # LLM handling (uses Groq API)
├── requirements_enhanced.txt       # Python dependencies
└── test_enhanced_rag.py           # Comprehensive test script
```

## 🎨 Features

### 1. Enhanced Document Processing

**Text Extraction:**
- Primary: `pdfplumber` (better text layout preservation)
- Fallback: `PyMuPDF` for compatibility
- Automatic detection of text quality

**Table Extraction:**
```python
# Automatic table detection and formatting
config.ENABLE_TABLE_EXTRACTION = True
config.TABLE_EXTRACTION_METHOD = "pdfplumber"  # or "camelot"
```

Tables are extracted and preserved in markdown format:
```
[TABLE]
Header1 | Header2 | Header3
Value1  | Value2  | Value3
[/TABLE]
```

**OCR for Scanned Pages:**
```python
config.ENABLE_OCR = True
config.OCR_DPI = 300  # High quality
```
Automatically detects image-based pages and applies Tesseract OCR.

**Image Understanding (Optional):**
```python
config.ENABLE_IMAGE_DESCRIPTION = True
```
Uses BLIP-2 to generate descriptions of images/diagrams.

### 2. Hybrid Search

Combines semantic similarity with keyword matching:

```python
# Semantic (70%) + Keyword (30%)
config.USE_HYBRID_SEARCH = True
config.SEMANTIC_WEIGHT = 0.7
```

**How it works:**
1. Semantic search finds contextually similar chunks
2. Keyword matching boosts chunks with exact query terms
3. Combined scoring retrieves most relevant results

### 3. Smart Chunking

- **Regular text**: Split using RecursiveCharacterTextSplitter
- **Tables**: Kept intact as single chunks
- **Mixed content**: Intelligently separated

```python
# Chunks maintain content type metadata
chunk.metadata = {
    'chunk_type': 'table',  # or 'text', 'image_desc'
    'has_tables': True,
    'needs_ocr': False
}
```

### 4. Enhanced Context Formatting

Context is formatted differently based on content type:

```
[Source 1: document.pdf, Page 3]
📊 TABLE DATA:
Quarter | Revenue | Profit
Q1      | $100M   | $20M

[Source 2: document.pdf, Page 5]
Regular text content here...
```

### 5. Better Query Understanding

**Follow-up Question Handling:**
```
User: "What is the company's revenue?"
Assistant: "According to the table on page 3..."

User: "How does that compare to last year?"  ← Automatically rewritten
→ "How does the company's revenue compare to last year?"
```

### 6. Conversation Memory

- Tracks conversation history per thread
- Automatically includes relevant context
- Configurable history length

```python
# Query with thread tracking
answer, sources = chatbot.query(
    question="Follow-up question",
    thread_id="user_123"
)

# Clear memory when needed
chatbot.clear_memory(thread_id="user_123")
```

## ⚙️ Configuration

### Resource Modes

**Lightweight Mode** (for limited resources):
```python
config.set_lightweight_mode()
# Enables: tables, basic OCR
# Disables: image descriptions
# Settings: smaller chunks, fewer results
```

**Full Features** (requires more resources):
```python
config.enable_all_features()
# Enables: everything including BLIP-2
# Settings: larger chunks, more results
```

### Key Settings

```python
# Chunking
config.CHUNK_SIZE = 512
config.CHUNK_OVERLAP = 100

# Retrieval
config.N_RESULTS = 8
config.SIMILARITY_THRESHOLD = 0.05

# Hybrid Search
config.USE_HYBRID_SEARCH = True
config.SEMANTIC_WEIGHT = 0.7  # 70% semantic, 30% keyword

# Multi-modal
config.ENABLE_TABLE_EXTRACTION = True
config.ENABLE_OCR = True
config.ENABLE_IMAGE_DESCRIPTION = False  # Resource intensive
```

## 📊 Performance

### Processing Time (Example: 20-page PDF)

| Feature | Time | Notes |
|---------|------|-------|
| Text extraction | 2-5s | pdfplumber |
| Table extraction | 5-10s | Per page with tables |
| OCR (if needed) | 30-60s | Per scanned page |
| Image description | 10-20s | Per image with BLIP-2 |

### Resource Requirements

**Minimum (Lightweight Mode):**
- RAM: 8GB
- GPU: Optional
- Storage: 5GB (models)

**Recommended (Full Features):**
- RAM: 16GB
- GPU: 8GB VRAM
- Storage: 15GB (models + BLIP-2)

## 🔄 Migration from Original System

### Step 1: Install Dependencies

```bash
pip install -r requirements_enhanced.txt
```

### Step 2: Update Imports

```python
# Old
from documents.rag import RAGChatbot, RAGConfig

# New
from enhanced_conversation import RAGChatbot
from enhanced_config import RAGConfig
```

### Step 3: Update Configuration

```python
# Old
config = RAGConfig()

# New
config = RAGConfig()
config.ENABLE_TABLE_EXTRACTION = True  # Enable new features
config.ENABLE_OCR = True
```

### Step 4: Re-index Documents

The enhanced system creates better chunks, so re-indexing is recommended:

```python
# This will use enhanced processing
chatbot.index_documents(pdf_path='document.pdf')
```

### Backward Compatibility

All original methods are still available:
- `query()` - works the same
- `clear_memory()` - unchanged
- `get_system_info()` - returns more info

## 🎯 Use Cases

### 1. Financial Document Analysis
```python
# Handles annual reports with tables
chatbot.query("What were the Q4 earnings?")
# → Extracts data from earnings tables
```

### 2. Technical Documentation
```python
# Processes diagrams and code tables
config.ENABLE_IMAGE_DESCRIPTION = True
chatbot.query("Explain the architecture diagram on page 5")
```

### 3. Research Papers
```python
# Handles complex tables and figures
chatbot.query("What do the experimental results show?")
# → Understands data tables and references them
```

### 4. Scanned Documents
```python
# OCR for old or scanned PDFs
config.ENABLE_OCR = True
chatbot.index_documents(pdf_path='scanned_contract.pdf')
```

## 🐛 Troubleshooting

### OCR Not Working
```bash
# Install Tesseract
sudo apt-get install tesseract-ocr

# Verify installation
tesseract --version
```

### Camelot Table Extraction Fails
```bash
# Install required system dependencies
sudo apt-get install ghostscript python3-tk
```

### Out of Memory
```python
# Use lightweight mode
config.set_lightweight_mode()

# Reduce batch size
config.EMBEDDING_BATCH_SIZE = 8

# Reduce chunk size
config.CHUNK_SIZE = 256
```

### BLIP-2 Model Loading Issues
```python
# Disable if not needed (saves ~3GB RAM)
config.ENABLE_IMAGE_DESCRIPTION = False
```

### Poor Table Extraction
```python
# Try Camelot instead of pdfplumber
config.TABLE_EXTRACTION_METHOD = "camelot"

# Or adjust settings
config.CHUNK_SIZE = 512  # Larger chunks for tables
```

## 📈 Future Enhancements

- [ ] Multi-column PDF layout handling
- [ ] Chart/graph data extraction with computer vision
- [ ] Excel/CSV file support
- [ ] Multi-lingual OCR
- [ ] Streaming responses for long answers
- [ ] Async document processing
- [ ] Query result caching
- [ ] Fine-tuning embeddings on domain data

## 📝 Notes

### Model Storage

Models are cached in:
- `~/.cache/huggingface/` (embeddings, BLIP-2)
- System default for Groq API (cloud-based)

### API Keys

Set in `.env` file:
```
GROQ_API_KEY=your_groq_key_here
```

### ChromaDB Storage

Vector embeddings stored in:
```
{CHROMA_DB_PATH}/
├── chroma.sqlite3
└── [collection_data]
```

## 🤝 Contributing

Improvements welcome! Areas of interest:
- Better table structure preservation
- Multi-modal embedding models
- Optimized OCR pipelines
- Advanced query understanding

## 📄 License

Part of DocuVault DMS project

---

**Built with:** pdfplumber, Camelot, Tesseract, BLIP-2, Sentence-Transformers, ChromaDB, LangChain, Groq