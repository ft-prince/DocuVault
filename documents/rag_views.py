"""
RAG Chatbot Views for DocuVault DMS
Handles chatbot interface, querying, and document indexing
"""

import os
import time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.conf import settings
from django.db.models import Q

from .models import (
    Document, ChatSession, ChatMessage, DocumentEmbedding,
    ActivityLog
)
from .forms import ChatQueryForm, DocumentIndexForm
from .rag import RAGChatbot, RAGConfig
from .rag.document_processor import DocumentProcessor


# Global RAG chatbot instance (lazy-loaded)
_rag_chatbot = None


def get_rag_chatbot():
    """Get or initialize the RAG chatbot instance"""
    global _rag_chatbot
    
    if _rag_chatbot is None:
        # Configure RAG
        config = RAGConfig()
        
        # Set ChromaDB path in media directory
        media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
        db_path = os.path.join(media_root, 'rag')
        config.set_chroma_path(db_path)
        
        # Initialize chatbot
        _rag_chatbot = RAGChatbot(config=config)
        _rag_chatbot.initialize(reset=False)
    
    return _rag_chatbot


@login_required
def chatbot_view(request):
    """
    Main chatbot interface
    """
    # Get or create active chat session for user
    chat_session = ChatSession.objects.filter(
        user=request.user,
        is_active=True
    ).first()
    
    if not chat_session:
        chat_session = ChatSession.objects.create(
            user=request.user,
            title='New Conversation'
        )
    
    # Get chat history
    messages_list = chat_session.messages.all()
    
    # Get user's accessible documents
    user_documents = Document.objects.filter(
        Q(access_level='public') |
        Q(owner=request.user) |
        Q(access_level='role', role_required__level__lte=request.user.get_role_level()) |
        Q(shared_users=request.user)
    ).filter(
        is_deleted=False
    )
    
    # Get indexed documents count
    indexed_count = DocumentEmbedding.objects.filter(
        document__in=user_documents,
        is_indexed=True
    ).count()
    
    context = {
        'chat_session': chat_session,
        'messages': messages_list,
        'total_documents': user_documents.count(),
        'indexed_documents': indexed_count,
        'form': ChatQueryForm()
    }
    
    return render(request, 'documents/chatbot.html', context)


@login_required
@require_http_methods(["POST"])
def chatbot_query_api(request):
    """
    API endpoint for chatbot queries
    Returns JSON response
    """
    form = ChatQueryForm(request.POST)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'error': 'Invalid query'
        }, status=400)
    
    question = form.cleaned_data['query']
    session_id = request.POST.get('session_id')
    
    # Get or create chat session
    if session_id:
        chat_session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    else:
        chat_session = ChatSession.objects.create(
            user=request.user,
            title=question[:50]  # Use first part of question as title
        )
    
    # Save user message
    user_message = ChatMessage.objects.create(
        session=chat_session,
        message_type='human',
        content=question
    )
    
    try:
        # Get RAG chatbot
        chatbot = get_rag_chatbot()
        
        # Get user's accessible documents for filtering
        accessible_docs = Document.objects.filter(
            Q(access_level='public') |
            Q(owner=request.user) |
            Q(access_level='role', role_required__level__lte=request.user.get_role_level()) |
            Q(shared_users=request.user)
        ).filter(
            is_deleted=False,
            embedding__is_indexed=True
        ).values_list('title', flat=True)
        
        # Measure retrieval time
        start_time = time.time()
        
        # Query the chatbot
        answer, sources = chatbot.query(
            question=question,
            use_rewrite=True
        )
        
        # Filter sources to only include accessible documents
        filtered_sources = [
            source for source in sources
            if any(doc in source.get('source', '') for doc in accessible_docs)
        ]
        
        retrieval_time = time.time() - start_time
        
        # Save AI response
        ai_message = ChatMessage.objects.create(
            session=chat_session,
            message_type='ai',
            content=answer,
            sources=filtered_sources,
            retrieval_time=retrieval_time,
            generation_time=retrieval_time
        )
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='chatbot_query',
            details=f"Query: {question[:100]}"
        )
        
        return JsonResponse({
            'success': True,
            'answer': answer,
            'sources': filtered_sources,
            'session_id': chat_session.id,
            'message_id': ai_message.id,
            'retrieval_time': round(retrieval_time, 2)
        })
        
    except Exception as e:
        # Save error message
        ChatMessage.objects.create(
            session=chat_session,
            message_type='system',
            content=f"Error: {str(e)}"
        )
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def chat_history_view(request):
    """View all chat sessions for the user"""
    chat_sessions = ChatSession.objects.filter(user=request.user)
    
    context = {
        'chat_sessions': chat_sessions
    }
    
    return render(request, 'documents/chat_history.html', context)


@login_required
def chat_session_detail_view(request, pk):
    """View details of a specific chat session"""
    chat_session = get_object_or_404(ChatSession, id=pk, user=request.user)
    messages_list = chat_session.messages.all()
    
    context = {
        'chat_session': chat_session,
        'messages': messages_list
    }
    
    return render(request, 'documents/chat_session_detail.html', context)


@login_required
@require_http_methods(["POST"])
def clear_chat_view(request):
    """Clear conversation history for current session"""
    session_id = request.POST.get('session_id')
    
    if session_id:
        chat_session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        chat_session.messages.all().delete()
        
        # Clear RAG chatbot memory
        try:
            chatbot = get_rag_chatbot()
            chatbot.clear_memory()
        except Exception:
            pass
        
        messages.success(request, 'Chat history cleared successfully.')
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid session'}, status=400)


@login_required
def document_index_view(request, pk):
    """
    Index a single document into the RAG system
    """
    document = get_object_or_404(Document, id=pk)
    
    # Check permissions
    if not (document.owner == request.user or 
            request.user.is_admin() or
            document.can_view(request.user)):
        messages.error(request, 'You do not have permission to index this document.')
        return redirect('document_detail', pk=pk)
    
    # Get or create embedding record
    embedding, created = DocumentEmbedding.objects.get_or_create(
        document=document
    )
    
    # Check if already indexed
    if embedding.is_indexed and not request.POST.get('force_reindex'):
        messages.info(request, f'Document "{document.title}" is already indexed.')
        return redirect('document_detail', pk=pk)
    
    # Mark as processing
    embedding.mark_processing()
    
    try:
        # Get document file path
        if not document.file:
            raise ValueError("Document has no file attached")
        
        file_path = document.file.path
        
        if not file_path.lower().endswith('.pdf'):
            raise ValueError("Only PDF documents can be indexed currently")
        
        # Load document
        processor = DocumentProcessor()
        documents = processor.load_single_document(file_path)
        
        # Get RAG chatbot and index
        chatbot = get_rag_chatbot()
        
        # Index the document
        chatbot.index_documents(documents)
        
        # Mark as completed
        embedding.mark_completed(
            chunk_count=len(documents),
            embedding_model=chatbot.config.EMBEDDING_MODEL
        )
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='document_indexed',
            document=document,
            details=f"Indexed document: {document.title}"
        )
        
        messages.success(request, f'Document "{document.title}" indexed successfully!')
        
    except Exception as e:
        embedding.mark_failed(str(e))
        messages.error(request, f'Failed to index document: {str(e)}')
    
    return redirect('document_detail', pk=pk)


@login_required
def bulk_index_documents_view(request):
    """
    Bulk index multiple documents
    """
    if request.method == 'POST':
        form = DocumentIndexForm(request.POST)
        
        if form.is_valid():
            document_ids = request.POST.getlist('document_ids')
            
            if not document_ids:
                messages.warning(request, 'No documents selected.')
                return redirect('bulk_index_documents')
            
            # Get documents
            documents = Document.objects.filter(
                id__in=document_ids,
                is_deleted=False
            )
            
            # Check permissions
            accessible_docs = documents.filter(
                Q(owner=request.user) |
                Q(access_level='public') |
                Q(access_level='role', role_required__level__lte=request.user.get_role_level()) |
                Q(shared_users=request.user)
            )
            
            indexed_count = 0
            failed_count = 0
            
            for doc in accessible_docs:
                embedding, created = DocumentEmbedding.objects.get_or_create(document=doc)
                
                # Skip if already indexed
                if embedding.is_indexed and not form.cleaned_data.get('force_reindex'):
                    continue
                
                embedding.mark_processing()
                
                try:
                    if not doc.file or not doc.file.path.lower().endswith('.pdf'):
                        raise ValueError("Invalid file type")
                    
                    processor = DocumentProcessor()
                    docs = processor.load_single_document(doc.file.path)
                    
                    chatbot = get_rag_chatbot()
                    chatbot.index_documents(docs)
                    
                    embedding.mark_completed(
                        chunk_count=len(docs),
                        embedding_model=chatbot.config.EMBEDDING_MODEL
                    )
                    indexed_count += 1
                    
                except Exception as e:
                    embedding.mark_failed(str(e))
                    failed_count += 1
            
            messages.success(request, f'Indexed {indexed_count} documents. Failed: {failed_count}')
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='bulk_index',
                details=f"Bulk indexed {indexed_count} documents"
            )
            
            return redirect('document_list')
    else:
        form = DocumentIndexForm()
    
    # Get user's documents
    user_documents = Document.objects.filter(
        Q(owner=request.user) |
        Q(access_level='public') |
        Q(access_level='role', role_required__level__lte=request.user.get_role_level()) |
        Q(shared_users=request.user)
    ).filter(is_deleted=False)
    
    context = {
        'form': form,
        'documents': user_documents
    }
    
    return render(request, 'documents/bulk_index.html', context)


@login_required
def rag_system_info_view(request):
    """Display RAG system information and statistics"""
    try:
        chatbot = get_rag_chatbot()
        system_info = chatbot.get_system_info()
    except Exception as e:
        system_info = {'error': str(e)}
    
    # Get statistics
    total_indexed = DocumentEmbedding.objects.filter(is_indexed=True).count()
    pending = DocumentEmbedding.objects.filter(index_status='pending').count()
    processing = DocumentEmbedding.objects.filter(index_status='processing').count()
    failed = DocumentEmbedding.objects.filter(index_status='failed').count()
    
    total_sessions = ChatSession.objects.filter(user=request.user).count()
    total_messages = ChatMessage.objects.filter(session__user=request.user).count()
    
    context = {
        'system_info': system_info,
        'total_indexed': total_indexed,
        'pending': pending,
        'processing': processing,
        'failed': failed,
        'total_sessions': total_sessions,
        'total_messages': total_messages
    }
    
    return render(request, 'documents/rag_system_info.html', context)
