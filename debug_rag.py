
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from documents.rag import RAGChatbot, RAGConfig
from documents.rag.document_processor import DocumentProcessor

def debug_rag_system():
    print("="*70)
    print("DEBUG RAG System")
    print("="*70)
    
    # Configure RAG
    config = RAGConfig()
    
    # Set ChromaDB path
    base_path = os.path.join(os.path.dirname(__file__), 'media')
    config.set_chroma_path(base_path)
    print(f"ChromaDB Path: {config.CHROMA_DB_PATH}")
    
    # Initialize chatbot
    chatbot = RAGChatbot(config=config)
    
    # Initialize with reset (for testing)
    chatbot.initialize(reset=True)
    
    # Check if we have documents to index
    pdf_dir = os.path.join(os.path.dirname(__file__), 'media', 'documents')
    print(f"Looking for documents in: {pdf_dir}")
    
    if os.path.exists(pdf_dir):
        # List files in directory
        files = os.listdir(pdf_dir)
        print(f"Files in directory: {files}")
        
        # Load documents
        processor = DocumentProcessor(config=config)
        
        # Try to load PDFs from directory
        try:
            documents = processor.load_documents_from_directory(pdf_dir)
            
            if documents:
                print(f"\nFound {len(documents)} document pages")
                for i, doc in enumerate(documents[:5]):
                    print(f"Doc {i}: Source={doc.metadata.get('source')}, Page={doc.metadata.get('page')}")
                
                # Index documents
                print("\nIndexing documents...")
                chatbot.index_documents(documents)
                
                # Verify indexing
                count = chatbot.vector_store.get_document_count()
                print(f"Total documents in vector store: {count}")
                
            else:
                print("\n⚠️ No PDF documents found.")
        except Exception as e:
            print(f"\n⚠️ Error loading documents: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"\n⚠️ Document directory not found: {pdf_dir}")
    
    # Test query
    question = "tell me about the renata AI push detection system"
    print(f"\nQuerying: {question}")
    
    try:
        # Query the chatbot
        answer, sources = chatbot.query(question)
        
        print(f"\n🤖 Assistant: {answer}")
        
        # Display sources
        if sources:
            print("\n📚 Sources:")
            for i, source in enumerate(sources, 1):
                print(f"{i}. {source['source']} (Page {source['page']}) - Relevance: {source['similarity']:.3f}")
                print(f"   Preview: {source['text_preview']}...")
        else:
            print("\n⚠️ No relevant sources found")
            
            # Debug retrieval directly
            print("\nDebugging retrieval directly...")
            query_embedding = chatbot.embedding_manager.get_embedding(question)
            results = chatbot.vector_store.query(query_embedding, n_results=10)
            print(f"Raw results: {results}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_rag_system()
