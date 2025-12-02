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
    # Check both media/documents and media root
    media_root = os.path.join(os.path.dirname(__file__), 'media')
    pdf_dir = os.path.join(media_root, 'documents')
    
    documents = []
    processor = DocumentProcessor(config=config)

    # 1. Check media/documents
    if os.path.exists(pdf_dir):
        print(f"\nChecking {pdf_dir}...")
        try:
            docs = processor.load_documents_from_directory(pdf_dir)
            documents.extend(docs)
        except Exception as e:
            print(f"Error loading from {pdf_dir}: {e}")
    
    # 2. Check media root (where user might have put the file)
    if os.path.exists(media_root):
        print(f"\nChecking {media_root}...")
        # Load individual PDFs from media root
        try:
            for file in os.listdir(media_root):
                if file.lower().endswith('.pdf'):
                    path = os.path.join(media_root, file)
                    print(f"Found PDF in media root: {file}")
                    docs = processor.load_single_document(path)
                    documents.extend(docs)
        except Exception as e:
            print(f"Error loading from {media_root}: {e}")

    if documents:
        print(f"\n✅ Found {len(documents)} total document pages")
        
        # Index documents
        print("\nIndexing documents...")
        chatbot.index_documents(documents)
    else:
        print("\n⚠️ No PDF documents found in media or media/documents.")
        print("Continuing with empty index for demo purposes...")
    
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
