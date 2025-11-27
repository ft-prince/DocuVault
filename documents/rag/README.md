# RAG Module Documentation

## Overview

This module provides a complete Retrieval-Augmented Generation (RAG) system for the DocuVault DMS. It enables intelligent document querying using semantic search and large language models.

## Architecture

```
documents/rag/
├── __init__.py              # Module exports
├── config.py                # Configuration settings
├── document_processor.py    # PDF loading and chunking
├── embeddings.py            # Embedding generation
├── vector_store.py          # ChromaDB vector database
├── llm_manager.py          # LLM loading and inference
├── retriever.py            # Query processing and retrieval
└── conversation.py         # Chatbot with memory
```

## Module Components

### 1. RAGConfig (`config.py`)
Central configuration for all RAG components.

**Key Settings:**
- `EMBEDDING_MODEL`: Qwen/Qwen3-Embedding-0.6B
- `LLM_MODEL`: Qwen/Qwen2.5-7B
- `CHUNK_SIZE`: 512 characters
- `CHUNK_OVERLAP`: 100 characters
- `SIMILARITY_THRESHOLD`: 0.15
- `MAX_NEW_TOKENS`: 512

### 2. DocumentProcessor (`document_processor.py`)
Handles document loading and text chunking.

**Key Methods:**
- `load_documents_from_directory(pdf_dir)`: Load all PDFs from directory
- `load_single_document(pdf_path)`: Load single PDF
- `split_documents(documents)`: Chunk documents for embedding
- `prepare_chunks_for_embedding(chunks)`: Extract texts and metadata

### 3. EmbeddingManager (`embeddings.py`)
Manages embedding model and generates embeddings.

**Key Methods:**
- `load_model()`: Load SentenceTransformer model
- `generate_embeddings(texts)`: Generate embeddings for multiple texts
- `generate_query_embedding(query)`: Generate single query embedding
- `get_embedding_dimension()`: Get embedding dimension

### 4. VectorStore (`vector_store.py`)
Manages ChromaDB vector database operations.

**Key Methods:**
- `initialize(db_path, reset)`: Setup ChromaDB
- `add_documents(embeddings, texts, metadatas, ids)`: Add documents
- `query(query_embedding, n_results)`: Search for similar documents
- `delete_documents(ids)`: Remove documents
- `filter_by_similarity(results, threshold)`: Filter by similarity score

### 5. LLMManager (`llm_manager.py`)
Handles LLM loading and text generation.

**Key Methods:**
- `load_model()`: Load quantized LLM
- `generate(messages, max_new_tokens, temperature)`: Generate response
- `rewrite_question(question, chat_history)`: Rewrite follow-up questions
- `get_model_info()`: Get model statistics

### 6. Retriever (`retriever.py`)
Query processing and document retrieval.

**Key Methods:**
- `retrieve(query, n_results, similarity_threshold)`: Retrieve relevant docs
- `rewrite_query(query, chat_history)`: Rewrite follow-up queries
- `format_context(documents, metadatas)`: Format context for LLM
- `prepare_sources(documents, metadatas, similarities)`: Format sources

### 7. RAGChatbot (`conversation.py`)
Main chatbot interface with conversation memory.

**Key Methods:**
- `initialize(db_path, reset)`: Initialize all components
- `index_documents(documents)`: Index documents into vector store
- `query(question, n_results, use_rewrite)`: Query with a question
- `clear_memory()`: Clear conversation history
- `get_conversation_history()`: Get chat history
- `get_system_info()`: Get system status

## Usage Example

```python
from documents.rag import RAGChatbot, RAGConfig
from documents.rag.document_processor import DocumentProcessor

# Configure
config = RAGConfig()
config.set_chroma_path('/path/to/vector/store')

# Initialize chatbot
chatbot = RAGChatbot(config=config)
chatbot.initialize(reset=False)

# Load and index documents
processor = DocumentProcessor(config=config)
documents = processor.load_documents_from_directory('/path/to/pdfs')
chatbot.index_documents(documents)

# Query
answer, sources = chatbot.query("What is this document about?")
print(f"Answer: {answer}")

for source in sources:
    print(f"Source: {source['source']}, Page: {source['page']}, Relevance: {source['similarity']}")

# Clear history
chatbot.clear_memory()
```

## Standalone Testing

Run the test script to verify the RAG system:

```bash
python test_rag.py
```

## Installation

Install additional dependencies:

```bash
pip install -r requirements_rag.txt
```

For GPU support (CUDA 11.8):
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

For CPU only:
```bash
pip install torch torchvision torchaudio
```

## Hardware Requirements

### Minimum (CPU only)
- RAM: 16GB
- Storage: 20GB for models
- Processing: Slow inference (~30s per query)

### Recommended (GPU)
- GPU: 8GB VRAM (RTX 3070 or better)
- RAM: 16GB
- Storage: 20GB for models
- Processing: Fast inference (~5s per query)

### Optimal (Production)
- GPU: 16GB+ VRAM (RTX 4090, A6000, etc.)
- RAM: 32GB
- Storage: 50GB
- Multiple GPUs for concurrent requests

## Configuration Options

### Chunking Parameters
```python
config.CHUNK_SIZE = 512          # Characters per chunk
config.CHUNK_OVERLAP = 100       # Overlap between chunks
```

### Retrieval Parameters
```python
config.N_RESULTS = 6             # Chunks to retrieve
config.SIMILARITY_THRESHOLD = 0.15  # Minimum relevance
```

### Generation Parameters
```python
config.MAX_NEW_TOKENS = 512      # Max response length
config.TEMPERATURE = 0.2         # Sampling temperature (0.0-1.0)
config.TOP_P = 0.85              # Nucleus sampling
config.REPETITION_PENALTY = 1.1  # Reduce repetition
```

### Memory Settings
```python
config.MAX_MEMORY_TOKEN_LIMIT = 2000  # Memory buffer size
config.MAX_HISTORY_TURNS = 6          # Turns in context
```

## Features

### ✅ Implemented
- PDF document loading and processing
- Text chunking with overlap
- Semantic embeddings (Qwen3-Embedding-0.6B)
- Vector storage (ChromaDB)
- Similarity search with thresholds
- LLM inference (Qwen2.5-7B, 8-bit quantized)
- Multi-turn conversations with memory
- Query rewriting for follow-ups
- Hallucination prevention (strict context adherence)
- Source tracking and citation
- Relevance scoring

### 🔄 Future Enhancements
- Django model integration
- Async processing with Celery
- User permission filtering
- Multi-document comparison
- Streaming responses
- Model fine-tuning
- Hybrid search (keyword + semantic)
- Multi-modal support (images, tables)

## Troubleshooting

### Out of Memory Error
- Reduce `CHUNK_SIZE`
- Lower `EMBEDDING_BATCH_SIZE`
- Use CPU for embeddings, GPU only for LLM
- Enable swap memory

### Slow Inference
- Use GPU instead of CPU
- Reduce `MAX_NEW_TOKENS`
- Lower `N_RESULTS`
- Consider smaller LLM (Qwen2.5-1.5B)

### Poor Retrieval Quality
- Increase `N_RESULTS`
- Lower `SIMILARITY_THRESHOLD`
- Adjust `CHUNK_SIZE` and `CHUNK_OVERLAP`
- Check document quality

### Model Download Issues
- Models are ~7GB each
- Ensure stable internet connection
- Check HuggingFace availability
- Consider pre-downloading models

## Model Storage

Models are downloaded to:
- Windows: `C:\Users\<username>\.cache\huggingface\`
- Linux/Mac: `~/.cache/huggingface/`

Total storage: ~15GB for both models

## Next Steps

1. ✅ **Code Modularization** - COMPLETED
2. Django Integration (models, views, URLs)
3. Celery for async indexing
4. Frontend UI
5. Permission-based retrieval
6. Production deployment

## Notes

- This is a self-contained module that can work standalone or with Django
- All code is type-hinted for better IDE support
- Comprehensive error handling included
- Configuration is centralized in `config.py`
- Memory-efficient with lazy loading
- Production-ready architecture

## License

Part of DocuVault DMS project
