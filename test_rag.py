"""
Standalone test script for RAG system
Tests the modular RAG implementation without Django
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from documents.rag import RAGChatbot, RAGConfig
from documents.rag.document_processor import DocumentProcessor


def test_rag_system():
    """Test the RAG system with sample documents"""
    
    print("="*70)
    print("RAG System Test")
    print("="*70)
    
    # Configure RAG
    config = RAGConfig()
    
    # Set ChromaDB path
    base_path = os.path.join(os.path.dirname(__file__), 'media')
    config.set_chroma_path(base_path)
    
    # Initialize chatbot
    chatbot = RAGChatbot(config=config)
    
    # Initialize with reset (for testing)
    chatbot.initialize(reset=True)
    
    # Check if we have documents to index
    pdf_dir = os.path.join(os.path.dirname(__file__), 'media', 'documents')
    
    if os.path.exists(pdf_dir):
        print(f"\nLooking for PDF documents in: {pdf_dir}")
        
        # Load documents
        processor = DocumentProcessor(config=config)
        
        # Try to load PDFs from directory
        try:
            documents = processor.load_documents_from_directory(pdf_dir)
            
            if documents:
                print(f"\nFound {len(documents)} document pages")
                
                # Index documents
                print("\nIndexing documents...")
                chatbot.index_documents(documents)
            else:
                print("\n⚠️ No PDF documents found. Please add PDFs to test.")
                print("Continuing with empty index for demo purposes...")
        except Exception as e:
            print(f"\n⚠️ Error loading documents: {e}")
            print("Continuing without indexing...")
    else:
        print(f"\n⚠️ Document directory not found: {pdf_dir}")
        print("Continuing without indexing...")
    
    # Test queries
    print("\n" + "="*70)
    print("Interactive RAG Chatbot")
    print("Type 'quit' to exit, 'clear' to reset history, 'info' for system info")
    print("="*70)
    
    while True:
        question = input("\n🧑 You: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if question.lower() == 'clear':
            chatbot.clear_memory()
            continue
        
        if question.lower() == 'info':
            info = chatbot.get_system_info()
            print("\n📊 System Information:")
            for key, value in info.items():
                print(f"  {key}: {value}")
            continue
        
        if not question:
            continue
        
        try:
            # Query the chatbot
            answer, sources = chatbot.query(question)
            
            print(f"\n🤖 Assistant: {answer}")
            
            # Display sources
            if sources:
                print("\n📚 Sources:")
                for i, source in enumerate(sources, 1):
                    quality = "🟢" if source['similarity'] > 0.3 else "🟡" if source['similarity'] > 0.15 else "🔴"
                    print(f"{i}. {quality} {source['source']} (Page {source['page']}) - Relevance: {source['similarity']:.3f}")
                    print(f"   Preview: {source['text_preview']}...")
            else:
                print("\n⚠️ No relevant sources found")
            
            # Show conversation stats
            history_len = len(chatbot.get_conversation_history())
            print(f"\n💬 [Chat history: {history_len//2} turn(s)]")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("Test completed")
    print("="*70)


if __name__ == "__main__":
    test_rag_system()
