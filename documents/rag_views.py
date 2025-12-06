"""
Enhanced RAG Views for Document Management System
RAG-specific views only - works with existing models
"""

import os
import time
from typing import Optional

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.conf import settings
from django.db.models import Q
from django.core.paginator import Paginator

from .models import (
    Document, ChatSession, ChatMessage, DocumentEmbedding,
    ActivityLog
)
from .forms import ChatQueryForm, DocumentIndexForm

# Import enhanced RAG components
from .rag.conversation import RAGChatbot
from .rag.config import RAGConfig
from .rag.document_processor import EnhancedDocumentProcessor


# ============================================================================
# RAG SYSTEM VIEWS
# ============================================================================

# Global chatbot instance
_rag_chatbot: Optional[RAGChatbot] = None


def get_rag_chatbot() -> RAGChatbot:
    """
    Get or initialize the enhanced RAG chatbot instance
    Lazy-loaded singleton pattern - same function name as original
    """
    global _rag_chatbot
    
    if _rag_chatbot is None:
        # Configure enhanced RAG
        config = RAGConfig()
        
        # Lightweight mode recommended for production
        config.set_lightweight_mode()
        
        # Customize settings
        config.ENABLE_TABLE_EXTRACTION = True
        config.ENABLE_OCR = True
        config.ENABLE_IMAGE_DESCRIPTION = False  # Disable to save resources
        config.USE_HYBRID_SEARCH = True
        
        # Set storage path
        media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
        db_path = os.path.join(media_root, 'rag')
        config.set_chroma_path(db_path)
        
        # Initialize chatbot
        _rag_chatbot = RAGChatbot(config=config)
        _rag_chatbot.initialize(reset=False)
    
    return _rag_chatbot


@login_required
def chatbot_view(request):
    """Main chatbot interface"""
    # Get or create active chat session
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
        Q(shared_with=request.user)
    ).filter(is_deleted=False).distinct()
    
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
        'form': ChatQueryForm(),
        'enhanced_rag': True
    }
    
    return render(request, 'rag/chatbot.html', context)


@login_required
@require_http_methods(["POST"])
def chatbot_query_api(request):
    """Enhanced API endpoint for chatbot queries"""
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
            title=question[:50]
        )
    
    # Save user message
    user_message = ChatMessage.objects.create(
        session=chat_session,
        message_type='human',
        content=question
    )
    
    try:
        # Get chatbot
        chatbot = get_rag_chatbot()
        
        # Get accessible documents for filtering
        accessible_docs = Document.objects.filter(
            Q(access_level='public') |
            Q(owner=request.user) |
            Q(shared_with=request.user)
        ).filter(
            is_deleted=False,
            embedding__is_indexed=True
        ).values_list('title', flat=True)
        
        # Measure time
        start_time = time.time()
        
        # Query with enhanced system
        answer, sources = chatbot.query(
            question=question,
            thread_id=str(chat_session.id)
        )
        
        retrieval_time = time.time() - start_time
        
        # Filter sources
        filtered_sources = [
            source for source in sources
            if any(doc in source.get('source', '') for doc in accessible_docs)
        ]
        
        # Enhanced logging
        print(f"\n{'='*70}")
        print(f"👤 User: {request.user.username}")
        print(f"💬 Query: {question}")
        print(f"🤖 Answer: {answer[:200]}...")
        
        if filtered_sources:
            print(f"\n📚 Sources ({len(filtered_sources)}):")
            for i, source in enumerate(filtered_sources[:5], 1):
                content_type = source.get('content_type', 'text')
                similarity = source.get('similarity', 0)
                icon = "📊" if content_type == 'table' else "🖼️" if content_type == 'image' else "📄"
                quality = "🟢" if similarity > 0.3 else "🟡" if similarity > 0.15 else "🔴"
                
                print(f"   {i}. {icon} {quality} {source.get('source')} (Page {source.get('page')})")
                print(f"      Type: {content_type} | Relevance: {similarity:.3f}")
        
        print(f"\n⏱️  Time: {retrieval_time:.2f}s")
        print(f"{'='*70}\n")
        
        # Save AI response
        ai_message = ChatMessage.objects.create(
            session=chat_session,
            message_type='ai',
            content=answer,
            sources=filtered_sources,
            retrieval_time=retrieval_time,
            generation_time=retrieval_time
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
    """View all chat sessions"""
    chat_sessions = ChatSession.objects.filter(user=request.user).order_by('-updated_at')
    
    paginator = Paginator(chat_sessions, 20)
    page = request.GET.get('page')
    sessions = paginator.get_page(page)
    
    context = {
        'chat_sessions': sessions
    }
    
    return render(request, 'rag/chat_history.html', context)


@login_required
def chat_session_detail_view(request, pk):
    """View details of a specific chat session"""
    chat_session = get_object_or_404(ChatSession, id=pk, user=request.user)
    messages_list = chat_session.messages.all()
    
    context = {
        'chat_session': chat_session,
        'messages': messages_list
    }
    
    return render(request, 'rag/chat_session_detail.html', context)


@login_required
@require_http_methods(["POST"])
def clear_chat_view(request):
    """Clear conversation history"""
    session_id = request.POST.get('session_id')
    
    if session_id:
        chat_session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        chat_session.messages.all().delete()
        
        try:
            chatbot = get_rag_chatbot()
            chatbot.clear_memory(thread_id=str(chat_session.id))
        except Exception:
            pass
        
        messages.success(request, 'Chat history cleared successfully.')
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid session'}, status=400)


@login_required
def document_index_view(request, pk):
    """Index a single document into RAG system"""
    document = get_object_or_404(Document, id=pk)
    
    # Check permissions
    if not (document.owner == request.user or 
            request.user.is_staff or
            document.can_view(request.user)):
        messages.error(request, 'You do not have permission to index this document.')
        return redirect('document_detail', pk=pk)
    
    # Get or create embedding
    embedding, created = DocumentEmbedding.objects.get_or_create(document=document)
    
    # Check if already indexed
    if embedding.is_indexed and not request.POST.get('force_reindex'):
        messages.info(request, f'Document "{document.title}" is already indexed.')
        return redirect('document_detail', pk=pk)
    
    embedding.mark_processing()
    
    try:
        if not document.file:
            raise ValueError("Document has no file attached")
        
        file_path = document.file.path
        
        if not file_path.lower().endswith('.pdf'):
            raise ValueError("Only PDF documents can be indexed currently")
        
        # Get chatbot
        chatbot = get_rag_chatbot()
        
        # Index with enhanced processing
        chatbot.index_documents(
            pdf_path=file_path,
            extract_tables=chatbot.config.ENABLE_TABLE_EXTRACTION,
            describe_images=chatbot.config.ENABLE_IMAGE_DESCRIPTION
        )
        
        # Get stats
        stats = chatbot.document_processor.get_processing_stats()
        
        # Mark completed
        embedding.mark_completed(
            chunk_count=stats.get('total_pages', 0),
            embedding_model=chatbot.config.EMBEDDING_MODEL
        )
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='edit',
            document=document,
            description=f"Indexed document: {document.title} "
                       f"({stats.get('total_pages', 0)} pages, "
                       f"{stats.get('tables_extracted', 0)} tables)"
        )
        
        messages.success(
            request,
            f'Document "{document.title}" indexed successfully! '
            f'Processed {stats.get("total_pages", 0)} pages.'
        )
        
    except Exception as e:
        embedding.mark_failed(str(e))
        messages.error(request, f'Failed to index document: {str(e)}')
    
    return redirect('document_detail', pk=pk)


@login_required
def bulk_index_documents_view(request):
    """Bulk index multiple documents"""
    if request.method == 'POST':
        form = DocumentIndexForm(request.POST)
        
        if form.is_valid():
            document_ids = request.POST.getlist('document_ids')
            
            if not document_ids:
                messages.warning(request, 'No documents selected.')
                return redirect('bulk_index_documents')
            
            documents = Document.objects.filter(
                id__in=document_ids,
                is_deleted=False
            )
            
            # Check permissions
            accessible_docs = documents.filter(
                Q(owner=request.user) |
                Q(access_level='public') |
                Q(shared_with=request.user)
            )
            
            indexed_count = 0
            failed_count = 0
            
            for doc in accessible_docs:
                embedding, created = DocumentEmbedding.objects.get_or_create(document=doc)
                
                if embedding.is_indexed and not form.cleaned_data.get('force_reindex'):
                    continue
                
                embedding.mark_processing()
                
                try:
                    if not doc.file or not doc.file.path.lower().endswith('.pdf'):
                        raise ValueError("Invalid file type")
                    
                    chatbot = get_rag_chatbot()
                    chatbot.index_documents(pdf_path=doc.file.path)
                    
                    stats = chatbot.document_processor.get_processing_stats()
                    embedding.mark_completed(
                        chunk_count=stats.get('total_pages', 0),
                        embedding_model=chatbot.config.EMBEDDING_MODEL
                    )
                    indexed_count += 1
                    
                except Exception as e:
                    embedding.mark_failed(str(e))
                    failed_count += 1
            
            messages.success(request, f'Indexed {indexed_count} documents. Failed: {failed_count}')
            return redirect('document_list')
    else:
        form = DocumentIndexForm()
    
    user_documents = Document.objects.filter(
        Q(owner=request.user) |
        Q(access_level='public') |
        Q(shared_with=request.user)
    ).filter(is_deleted=False)
    
    context = {
        'form': form,
        'documents': user_documents
    }
    
    return render(request, 'rag/bulk_index.html', context)


@login_required
def rag_system_info_view(request):
    """Display RAG system information"""
    try:
        chatbot = get_rag_chatbot()
        system_info = chatbot.get_system_info()
    except Exception as e:
        system_info = {'error': str(e)}
    
    # Statistics
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
    
    return render(request, 'rag/rag_system_info.html', context)


@login_required
@require_http_methods(["POST"])
def api_toggle_rag_feature(request):
    """Toggle RAG features (admin only)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    feature = request.POST.get('feature')
    enabled = request.POST.get('enabled') == 'true'
    
    try:
        chatbot = get_rag_chatbot()
        config = chatbot.config
        
        if feature == 'table_extraction':
            config.ENABLE_TABLE_EXTRACTION = enabled
        elif feature == 'ocr':
            config.ENABLE_OCR = enabled
        elif feature == 'image_description':
            config.ENABLE_IMAGE_DESCRIPTION = enabled
        elif feature == 'hybrid_search':
            config.USE_HYBRID_SEARCH = enabled
        else:
            return JsonResponse({'success': False, 'error': 'Unknown feature'})
        
        return JsonResponse({
            'success': True,
            'feature': feature,
            'enabled': enabled
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)