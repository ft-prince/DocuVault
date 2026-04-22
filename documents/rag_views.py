"""
Enhanced RAG Views for Document Management System
RAG-specific views only - works with existing models
"""

import json
import os
import sys
import time
import tempfile
from typing import Optional, List, Dict


def _safe_print(*args, **kwargs):
    """Print with Unicode-safe fallback for Windows consoles."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        text = ' '.join(str(a) for a in args)
        print(text.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(
            sys.stdout.encoding or 'utf-8', errors='replace'), **kwargs)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.conf import settings
from django.db.models import Q
from django.core.paginator import Paginator

from .models import (
    Document, ChatSession, ChatMessage, DocumentEmbedding,
    ActivityLog
)


def _enrich_sources(sources: List[Dict]) -> List[Dict]:
    """
    Replace raw file paths in sources with human-readable document titles.
    Falls back to the filename if no matching Document record is found.
    """
    if not sources:
        return sources

    # Build a path→title lookup once for all sources
    path_to_title: Dict[str, str] = {}
    for doc in Document.objects.filter(is_deleted=False).exclude(file=''):
        try:
            path_to_title[doc.file.path] = doc.title
        except Exception:
            pass

    enriched = []
    for src in sources:
        raw_path = src.get('source', '')
        # Try exact path match, then basename match
        title = (
            path_to_title.get(raw_path)
            or next(
                (t for p, t in path_to_title.items()
                 if os.path.basename(p) == os.path.basename(raw_path)),
                None,
            )
            or os.path.splitext(os.path.basename(raw_path))[0]
            or raw_path
        )
        enriched.append({**src, 'document_title': title})
    return enriched
from .forms import ChatQueryForm, DocumentIndexForm

# Import enhanced RAG components
from .rag.conversation import RAGChatbot
from .rag.config import RAGConfig
from .rag.document_processor import EnhancedDocumentProcessor


# ============================================================================
# RAG SYSTEM VIEWS
# ============================================================================

# Global chatbot instance + lock so only one thread ever calls initialize()
import threading as _threading
_rag_chatbot: Optional[RAGChatbot] = None
_rag_init_lock = _threading.Lock()


def get_rag_chatbot() -> RAGChatbot:
    """
    Get or initialize the enhanced RAG chatbot instance.
    Thread-safe: uses a lock so concurrent callers (e.g. background indexing
    threads fired by post_save signals) never race through initialization.
    """
    global _rag_chatbot

    # Fast path — already initialized, no lock needed
    if _rag_chatbot is not None and _rag_chatbot.is_initialized:
        return _rag_chatbot

    # Slow path — one thread initializes, the rest wait
    with _rag_init_lock:
        # Re-check inside the lock (another thread may have finished while we waited)
        if _rag_chatbot is not None and _rag_chatbot.is_initialized:
            return _rag_chatbot

        # Configure enhanced RAG
        config = RAGConfig()

        # Lightweight mode recommended for production
        config.set_lightweight_mode()

        # Overrides — keep lightweight but retrieve more chunks so multi-page
        # documents (stories, reports) surface all relevant sections.
        config.ENABLE_TABLE_EXTRACTION = True
        config.ENABLE_OCR = True
        config.ENABLE_IMAGE_DESCRIPTION = False
        config.USE_HYBRID_SEARCH = True
        config.N_RESULTS = 20
        config.SIMILARITY_THRESHOLD = -0.2

        # Set storage path
        media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
        db_path = os.path.join(media_root, 'rag')
        config.set_chroma_path(db_path)

        # Initialize chatbot (slow — loads embedding model + LLM)
        _rag_chatbot = RAGChatbot(config=config)
        _rag_chatbot.initialize(reset=False)

    return _rag_chatbot


@login_required
def chatbot_view(request):
    """Main chatbot interface with session history sidebar"""
    from datetime import date, timedelta

    # Load a specific session if requested via ?session=<id>
    session_id = request.GET.get('session')
    chat_session = None
    if session_id:
        try:
            chat_session = ChatSession.objects.get(id=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            chat_session = None

    if not chat_session:
        chat_session = (
            ChatSession.objects
            .filter(user=request.user, is_active=True)
            .order_by('-updated_at')
            .first()
        )

    if not chat_session:
        chat_session = ChatSession.objects.create(
            user=request.user,
            title='New Conversation'
        )

    # Messages for the active session
    messages_list = chat_session.messages.all()

    # Accessible documents — scoped to the user's organization
    org = getattr(request.user, 'organization', None)
    org_filter = Q(owner__organization=org) if org else Q(owner=request.user)
    user_documents = Document.objects.filter(
        org_filter,
        Q(access_level='public') | Q(owner=request.user) | Q(shared_with=request.user)
    ).filter(is_deleted=False).distinct()

    indexed_count = DocumentEmbedding.objects.filter(
        document__in=user_documents,
        is_indexed=True
    ).count()

    # Build grouped session list for sidebar (Today / Yesterday / This Week / Older)
    today     = date.today()
    yesterday = today - timedelta(days=1)
    week_ago  = today - timedelta(days=7)

    all_sessions_qs = (
        ChatSession.objects
        .filter(user=request.user)
        .order_by('-updated_at')[:80]
    )

    grouped_sessions = []
    current_group = None
    for s in all_sessions_qs:
        d = s.updated_at.date()
        if d == today:
            group = 'Today'
        elif d == yesterday:
            group = 'Yesterday'
        elif d > week_ago:
            group = 'This Week'
        else:
            group = 'Older'
        if group != current_group:
            current_group = group
            grouped_sessions.append({'type': 'header', 'label': group})
        grouped_sessions.append({'type': 'session', 'session': s})

    context = {
        'chat_session':     chat_session,
        'chat_messages':    messages_list,
        'total_documents':  user_documents.count(),
        'indexed_documents': indexed_count,
        'form':             ChatQueryForm(),
        'enhanced_rag':     True,
        'grouped_sessions': grouped_sessions,
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
        
        # Resolve org — used for both DB filtering and ChromaDB metadata filter
        org = getattr(request.user, 'organization', None)
        org_id = str(org.id) if org else f'user_{request.user.id}'
        org_filter = Q(owner__organization=org) if org else Q(owner=request.user)

        # Build accessible file-path set (OS path + basename) for source filtering
        _acc_qs = Document.objects.filter(
            org_filter,
            Q(access_level='public') | Q(owner=request.user) | Q(shared_with=request.user),
            is_deleted=False, embedding__is_indexed=True,
        ).exclude(file='')
        accessible_paths = set()
        for _d in _acc_qs:
            try:
                _p = _d.file.path
                accessible_paths.add(_p)
                accessible_paths.add(os.path.basename(_p))
            except Exception:
                pass

        start_time = time.time()
        answer, sources = chatbot.query(
            question=question,
            thread_id=str(chat_session.id),
            org_id=org_id,
        )
        retrieval_time = time.time() - start_time

        # Filter sources — match by path OR basename
        filtered_sources = [
            s for s in sources
            if not accessible_paths or
               s.get('source', '') in accessible_paths or
               os.path.basename(s.get('source', '')) in accessible_paths
        ]

        # Enrich sources with human-readable document titles
        filtered_sources = _enrich_sources(filtered_sources)
        
        # Enhanced logging
        _safe_print(f"\n{'='*70}")
        _safe_print(f"User: {request.user.username}")
        _safe_print(f"Query: {question}")
        _safe_print(f"Answer: {answer[:200]}...")

        if filtered_sources:
            _safe_print(f"\nSources ({len(filtered_sources)}):")
            for i, source in enumerate(filtered_sources[:5], 1):
                content_type = source.get('content_type', 'text')
                similarity = source.get('similarity', 0)

                _safe_print(f"   {i}. {source.get('source')} (Page {source.get('page')})")
                _safe_print(f"      Type: {content_type} | Relevance: {similarity:.3f}")

        _safe_print(f"\nTime: {retrieval_time:.2f}s")
        _safe_print(f"{'='*70}\n")
        
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
            'from_documents': len(filtered_sources) > 0,
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
def reindex_document_api(request, pk):
    """
    Force re-index a single document (any supported type) via AJAX POST.
    Resets is_indexed so the background thread picks it up fresh.
    Returns JSON: { success, message }
    """
    document = get_object_or_404(Document, pk=pk)
    if not (document.owner == request.user or request.user.is_staff or document.can_view(request.user)):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    if not document.file:
        return JsonResponse({'success': False, 'error': 'Document has no file attached'}, status=400)

    ext = os.path.splitext(document.file.name)[1].lower()
    from .signals import SUPPORTED_EXTENSIONS
    if ext not in SUPPORTED_EXTENSIONS:
        return JsonResponse({'success': False, 'error': f'File type {ext} not supported for indexing'}, status=400)

    # Reset status so _index_in_background will re-run
    embedding, _ = DocumentEmbedding.objects.get_or_create(document=document)
    embedding.is_indexed = False
    embedding.index_status = 'pending'
    embedding.save(update_fields=['is_indexed', 'index_status'])

    from .signals import _index_in_background
    import threading
    t = threading.Thread(target=_index_in_background, args=(document.id,), daemon=True)
    t.start()

    return JsonResponse({'success': True, 'message': f'Re-indexing started for "{document.title}" ({ext})'})


@login_required
@require_http_methods(["GET"])
def document_index_status_view(request, pk):
    """
    AJAX: return current indexing status for a document.
    Returns JSON: { status, is_indexed, chunk_count, error_message }
    """
    document = get_object_or_404(Document, pk=pk, is_deleted=False)
    if not document.can_view(request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        emb = DocumentEmbedding.objects.get(document=document)
        return JsonResponse({
            'status': emb.index_status,
            'is_indexed': emb.is_indexed,
            'chunk_count': emb.chunk_count,
            'error_message': emb.error_message or '',
        })
    except DocumentEmbedding.DoesNotExist:
        # No embedding record — file may not be a supported type
        from .signals import SUPPORTED_EXTENSIONS
        ext = os.path.splitext(document.file.name)[1].lower() if document.file else ''
        if ext in SUPPORTED_EXTENSIONS:
            return JsonResponse({'status': 'pending', 'is_indexed': False, 'chunk_count': 0, 'error_message': ''})
        return JsonResponse({'status': 'unsupported', 'is_indexed': False, 'chunk_count': 0, 'error_message': f'File type {ext} not supported'})


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
@require_http_methods(["POST"])
def new_chat_view(request):
    """Create a new chat session, return its id as JSON."""
    session = ChatSession.objects.create(
        user=request.user,
        title='New Conversation',
    )
    return JsonResponse({'ok': True, 'session_id': session.id})


@login_required
@require_http_methods(["POST"])
def delete_session_view(request, pk):
    """Delete a chat session and its RAG memory."""
    session = get_object_or_404(ChatSession, id=pk, user=request.user)
    try:
        chatbot = get_rag_chatbot()
        chatbot.clear_memory(thread_id=str(session.id))
    except Exception:
        pass
    session.delete()
    return JsonResponse({'ok': True})


@login_required
@require_http_methods(["POST"])
def rename_session_view(request, pk):
    """Rename a chat session title."""
    session = get_object_or_404(ChatSession, id=pk, user=request.user)
    try:
        data = json.loads(request.body)
        title = data.get('title', '').strip()
        if title:
            session.title = title[:100]
            session.save(update_fields=['title'])
    except Exception:
        pass
    return JsonResponse({'ok': True})


@login_required
@require_http_methods(["GET", "POST"])
def share_chat_view(request, pk):
    """
    GET  – return list of org members + current share state (JSON).
    POST – add or remove a share for the given user id.
    """
    from .models import ChatSessionShare, User

    session = get_object_or_404(ChatSession, id=pk, user=request.user)
    org = getattr(request.user, 'organization', None)

    if request.method == 'GET':
        # Org members excluding the owner
        if org:
            members = User.objects.filter(organization=org).exclude(id=request.user.id)
        else:
            members = User.objects.none()

        already_shared = set(
            ChatSessionShare.objects.filter(session=session).values_list('shared_with_id', flat=True)
        )

        data = [
            {
                'id': u.id,
                'name': u.get_full_name() or u.username,
                'username': u.username,
                'shared': u.id in already_shared,
            }
            for u in members
        ]
        return JsonResponse({'ok': True, 'members': data})

    # POST – toggle share for one user
    try:
        body = json.loads(request.body)
        user_id = int(body.get('user_id', 0))
        action = body.get('action', 'add')   # 'add' or 'remove'
    except (ValueError, TypeError):
        return JsonResponse({'ok': False, 'error': 'Invalid payload'}, status=400)

    target = get_object_or_404(User, id=user_id)

    # Enforce org boundary
    if org and target.organization != org:
        return JsonResponse({'ok': False, 'error': 'User not in your organization'}, status=403)

    if action == 'add':
        share_obj, created = ChatSessionShare.objects.get_or_create(
            session=session, shared_with=target,
            defaults={'shared_by': request.user}
        )
        # Fire notification only when a new share is created
        if created:
            from .models import Notification
            sender_name = request.user.get_full_name() or request.user.username
            Notification.objects.create(
                recipient=target,
                sender=request.user,
                notification_type='chat_shared',
                title='Chat Shared With You',
                message=f'{sender_name} shared a conversation with you: "{session.title}"',
                chat_session=session,
            )
    else:
        ChatSessionShare.objects.filter(session=session, shared_with=target).delete()

    return JsonResponse({'ok': True})


@login_required
def shared_with_me_view(request):
    """Chatbot-style page listing all chat sessions shared with the current user."""
    from .models import ChatSessionShare

    shares = (
        ChatSessionShare.objects
        .filter(shared_with=request.user)
        .select_related('session', 'shared_by')
        .order_by('-created_at')
    )
    return render(request, 'rag/shared_with_me.html', {'shares': shares})


@login_required
def view_shared_chat_view(request, pk):
    """Read-only view of a chat session shared with the current user."""
    from .models import ChatSessionShare

    # Gracefully handle nonexistent session or unauthorized access
    try:
        session = ChatSession.objects.get(id=pk)
    except ChatSession.DoesNotExist:
        messages.error(request, 'This conversation does not exist or the link has expired.')
        return redirect('chatbot')

    is_owner = session.user == request.user
    is_shared = ChatSessionShare.objects.filter(session=session, shared_with=request.user).exists()

    if not (is_owner or is_shared):
        messages.error(request, 'You do not have access to this conversation.')
        return redirect('chatbot')

    messages_list = session.messages.all()
    return render(request, 'rag/shared_chat.html', {
        'session': session,
        'chat_messages': messages_list,
        'is_owner': is_owner,
        'owner': session.user,
    })


@login_required
@require_http_methods(["POST"])
def toggle_public_share_view(request, pk):
    """
    POST — enable or disable the public share link for a chat session.
    Returns the share URL when enabled, null when disabled.
    """
    import uuid as _uuid
    session = get_object_or_404(ChatSession, id=pk, user=request.user)
    try:
        body  = json.loads(request.body)
        enable = body.get('enable', True)
    except Exception:
        enable = True

    if enable:
        if not session.public_share_token:
            session.public_share_token = _uuid.uuid4()
            session.save(update_fields=['public_share_token'])
        token = str(session.public_share_token)
        url   = request.build_absolute_uri(f'/chatbot/public/{token}/')
        return JsonResponse({'ok': True, 'enabled': True, 'token': token, 'url': url})
    else:
        session.public_share_token = None
        session.save(update_fields=['public_share_token'])
        return JsonResponse({'ok': True, 'enabled': False, 'token': None, 'url': None})


def public_chat_view(request, token):
    """
    Public read-only view — no login required.
    Accessible by anyone who has the link (like ChatGPT sharing).
    """
    try:
        session = ChatSession.objects.get(public_share_token=token)
    except ChatSession.DoesNotExist:
        return render(request, 'rag/public_chat_not_found.html', status=404)

    messages_list = session.messages.all()
    return render(request, 'rag/shared_chat.html', {
        'session':       session,
        'chat_messages': messages_list,
        'is_owner':      request.user.is_authenticated and session.user == request.user,
        'owner':         session.user,
        'is_public_view': True,
    })


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
        ext = os.path.splitext(file_path)[1].lower()

        from .signals import SUPPORTED_EXTENSIONS, _load_text_file, _load_docx_file
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}")

        chatbot = get_rag_chatbot()

        if ext == '.pdf':
            chatbot.index_documents(
                pdf_path=file_path,
                extract_tables=chatbot.config.ENABLE_TABLE_EXTRACTION,
                describe_images=chatbot.config.ENABLE_IMAGE_DESCRIPTION,
            )
            stats = chatbot.document_processor.get_processing_stats()
            chunk_count = stats.get('total_pages', 0)
        elif ext in {'.txt', '.md', '.text'}:
            lc_docs = _load_text_file(file_path, document)
            if not lc_docs:
                raise ValueError("File appears to be empty")
            chatbot.index_documents(documents=lc_docs)
            chunk_count = len(lc_docs)
        elif ext in {'.docx', '.doc'}:
            lc_docs = _load_docx_file(file_path, document)
            if not lc_docs:
                raise ValueError("Could not extract text from .docx file")
            chatbot.index_documents(documents=lc_docs)
            chunk_count = len(lc_docs)

        embedding.mark_completed(
            chunk_count=chunk_count,
            embedding_model=chatbot.config.EMBEDDING_MODEL,
        )
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='edit',
            document=document,
            description=f"Indexed document: {document.title} ({chunk_count} chunks, {ext})"
        )
        
        messages.success(
            request,
            f'Document "{document.title}" indexed successfully! '
            f'Processed {chunk_count} chunks.'
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


# ============================================================================
# STREAMING CHAT ENDPOINT
# ============================================================================

@login_required
@require_http_methods(["POST"])
def chatbot_query_stream_view(request):
    """
    Server-Sent Events endpoint — streams LLM tokens to the browser as they arrive.
    The client uses fetch() + ReadableStream to consume the SSE data.
    """
    question    = request.POST.get('query', '').strip()
    session_id  = request.POST.get('session_id', '')
    reply_lang  = request.POST.get('reply_lang', '').strip() or None  # e.g. 'hi-IN' in translate mode

    if not question:
        return JsonResponse({'error': 'Empty query'}, status=400)

    # Resolve / create session
    if session_id:
        try:
            chat_session = ChatSession.objects.get(id=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            chat_session = ChatSession.objects.create(user=request.user, title=question[:50])
    else:
        chat_session = ChatSession.objects.create(user=request.user, title=question[:50])

    # Save the human message before streaming starts
    ChatMessage.objects.create(
        session=chat_session,
        message_type='human',
        content=question,
    )

    # Auto-title session on first user message
    if chat_session.title == 'New Conversation':
        human_count = chat_session.messages.filter(message_type='human').count()
        if human_count <= 1:
            chat_session.title = question[:60]
            chat_session.save(update_fields=['title'])

    # Precompute accessible doc FILE PATHS for source filtering.
    # We must match file paths (not titles) because ChromaDB stores the OS
    # path as the 'source' field — UUID-based filenames never contain the title.
    _accessible_qs = Document.objects.filter(
        Q(access_level='public') | Q(owner=request.user) | Q(shared_with=request.user),
        is_deleted=False,
    ).exclude(file='')
    # Build both full OS paths and bare basenames so we handle any stored format.
    accessible_docs = set()
    for _doc in _accessible_qs:
        try:
            _p = _doc.file.path
            accessible_docs.add(_p)
            accessible_docs.add(os.path.basename(_p))
        except Exception:
            pass

    def sse_generator():
        # Send session id first so JS can use it immediately
        yield f"data: {json.dumps({'type': 'session', 'session_id': chat_session.id})}\n\n"
        yield f"data: {json.dumps({'type': 'title', 'session_id': chat_session.id, 'title': chat_session.title})}\n\n"

        try:
            chatbot = get_rag_chatbot()
            full_answer = ""
            sources = []
            start_time = time.time()

            for event in chatbot.query_stream(
                question=question,
                thread_id=str(chat_session.id),
                reply_lang=reply_lang,
                use_rewrite=False,  # Disabled: rewriter causes wrong chunks when history is polluted
            ):
                etype = event['type']

                if etype == 'sources':
                    raw = event['data']
                    # Filter to accessible docs then enrich.
                    # Match full path OR basename against the accessible set.
                    if accessible_docs:
                        def _accessible(src_path):
                            return (src_path in accessible_docs or
                                    os.path.basename(src_path) in accessible_docs)
                        raw = [s for s in raw if _accessible(s.get('source', ''))]
                    sources = _enrich_sources(raw)
                    yield f"data: {json.dumps({'type': 'sources', 'data': sources})}\n\n"

                elif etype == 'token':
                    full_answer += event['data']
                    yield f"data: {json.dumps({'type': 'token', 'data': event['data']})}\n\n"

                elif etype == 'done':
                    elapsed = round(time.time() - start_time, 2)
                    ai_msg = ChatMessage.objects.create(
                        session=chat_session,
                        message_type='ai',
                        content=full_answer,
                        sources=sources,
                        retrieval_time=elapsed,
                        generation_time=elapsed,
                    )
                    yield f"data: {json.dumps({'type': 'done', 'message_id': ai_msg.id, 'from_documents': len(sources) > 0})}\n\n"

                elif etype == 'error':
                    yield f"data: {json.dumps({'type': 'error', 'data': event['data']})}\n\n"

        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'data': str(exc)})}\n\n"

    response = StreamingHttpResponse(sse_generator(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # Disable nginx buffering
    return response


# ============================================================================
# VOICE TRANSCRIPTION ENDPOINT  (server-side Whisper fallback)
# ============================================================================

@login_required
@require_http_methods(["POST"])
def voice_transcribe_view(request):
    """
    Transcribe an audio blob (webm / wav) using Whisper.
    Used as a fallback when the browser's Web Speech API is unavailable.
    Primary STT is handled client-side via the Web Speech API.
    """
    audio_file = request.FILES.get('audio')
    if not audio_file:
        return JsonResponse({'error': 'No audio file provided'}, status=400)

    suffix = '.webm' if 'webm' in (audio_file.content_type or '') else '.wav'

    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            for chunk in audio_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        text = _transcribe_audio(tmp_path)
        return JsonResponse({'success': True, 'text': text})

    except Exception as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=500)

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def _transcribe_audio(path: str) -> str:
    """Transcribe audio file using faster-whisper (preferred) or openai-whisper."""
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(path, language="en")
        return " ".join(seg.text for seg in segments).strip()
    except ImportError:
        pass

    try:
        import whisper
        model = whisper.load_model("tiny")
        result = model.transcribe(path)
        return result["text"].strip()
    except ImportError:
        pass

    raise RuntimeError(
        "No Whisper backend found. Install faster-whisper: pip install faster-whisper"
    )


# ============================================================================
# VOICE ASSISTANT PAGE  (server-side STT + edge-tts TTS)
# ============================================================================

# Microsoft Neural voice mapping for Indian languages
_EDGE_VOICES = {
    'en-IN': 'en-IN-NeerjaNeural',
    'en-US': 'en-IN-NeerjaNeural',   # always use Indian English — not US accent
    'hi-IN': 'hi-IN-SwaraNeural',
    'ta-IN': 'ta-IN-PallaviNeural',
    'te-IN': 'te-IN-ShrutiNeural',
    'bn-IN': 'bn-IN-TanishaaNeural',
    'mr-IN': 'mr-IN-AarohiNeural',
    'gu-IN': 'gu-IN-DhwaniNeural',
    'kn-IN': 'kn-IN-SapnaNeural',
    'ml-IN': 'ml-IN-SobhanaNeural',
    'pa-IN': 'pa-IN-OjasNeural',
    'ur-IN': 'ur-IN-UzmaNeural',
}


def _edge_tts_synthesize(text: str, voice: str, rate: str = '+10%') -> bytes:
    """
    Synchronous wrapper around edge-tts async API.
    Returns raw MP3 bytes.
    """
    import asyncio
    import edge_tts

    async def _run():
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        chunks = []
        async for chunk in communicate.stream():
            if chunk['type'] == 'audio':
                chunks.append(chunk['data'])
        return b''.join(chunks)

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()


@login_required
def voice_assistant_view(request):
    """Dedicated voice assistant page — server-side Whisper STT + edge-tts TTS."""
    chat_session, _ = ChatSession.objects.get_or_create(
        user=request.user,
        title='Voice Assistant',
    )
    return render(request, 'rag/voice_assistant.html', {
        'chat_session': chat_session,
        'csrf_token': request.META.get('CSRF_COOKIE', ''),
    })


@login_required
@require_http_methods(["POST"])
def voice_assistant_transcribe_view(request):
    """
    STT endpoint for the voice assistant page.
    Expects a 16-kHz mono WAV blob (converted client-side — no ffmpeg needed).
    Falls back gracefully if faster-whisper is unavailable.
    """
    audio_file = request.FILES.get('audio')
    if not audio_file:
        return JsonResponse({'error': 'No audio provided'}, status=400)

    lang_hint = request.POST.get('lang', '')
    whisper_lang = lang_hint[:2] if lang_hint else None

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            for chunk in audio_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        text, detected_lang = _whisper_from_wav(tmp_path, whisper_lang)
        return JsonResponse({'success': True, 'text': text, 'detected_lang': detected_lang})

    except Exception as exc:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(exc)}, status=500)
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def _whisper_from_wav(wav_path: str, language: Optional[str] = None):
    """
    Transcribe a 16-kHz mono WAV using faster-whisper.
    Reads via Python's built-in 'wave' module — no ffmpeg required.

    Hinglish handling:
      - Never force language when input looks Hinglish (Latin-script Hindi).
      - Use initial_prompt to bias Whisper toward Hinglish transcription.
    Returns (text, detected_language).
    """
    import wave
    import numpy as np

    with wave.open(wav_path, 'rb') as wf:
        n_channels   = wf.getnchannels()
        sample_width = wf.getsampwidth()
        frame_rate   = wf.getframerate()
        raw_frames   = wf.readframes(wf.getnframes())

    if sample_width == 2:
        pcm = np.frombuffer(raw_frames, dtype=np.int16).astype(np.float32) / 32768.0
    elif sample_width == 4:
        pcm = np.frombuffer(raw_frames, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        pcm = np.frombuffer(raw_frames, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0

    if n_channels > 1:
        pcm = pcm.reshape(-1, n_channels).mean(axis=1)

    if frame_rate != 16000:
        from scipy.signal import resample_poly
        from math import gcd
        g = gcd(frame_rate, 16000)
        pcm = resample_poly(pcm, 16000 // g, frame_rate // g).astype(np.float32)

    from faster_whisper import WhisperModel
    global _whisper_model
    if _whisper_model is None:
        # 'small' handles Hinglish / multilingual significantly better than 'base'
        _whisper_model = WhisperModel("small", device="cpu", compute_type="int8")

    # For Indian languages (especially hi-IN) let Whisper auto-detect —
    # forcing 'hi' on Hinglish causes hallucinations. Use initial_prompt instead.
    indian_langs = {'hi', 'ta', 'te', 'bn', 'mr', 'gu', 'kn', 'ml', 'pa', 'ur'}
    opts = {
        "beam_size": 5,
        "temperature": 0.0,
        "vad_filter": True,        # skip silent segments (speeds up + reduces noise)
        "vad_parameters": {"min_silence_duration_ms": 500},
    }

    if language and language not in indian_langs:
        # Non-Indian forced language (e.g. 'en') — honour it
        opts["language"] = language
    elif language in indian_langs:
        # Indian language hint: don't force, but bias with initial_prompt
        opts["initial_prompt"] = (
            "The following is a spoken query in Indian English, Hindi, or Hinglish "
            "(a mix of Hindi and English spoken in India)."
        )
        # Do NOT set opts["language"] → let Whisper auto-detect
    # else: no hint at all → full auto-detect

    segments, info = _whisper_model.transcribe(pcm, **opts)
    text = " ".join(seg.text for seg in segments).strip()
    return text, info.language

_whisper_model = None


@login_required
@require_http_methods(["POST"])
def voice_synthesize_view(request):
    """
    TTS endpoint using edge-tts (Microsoft Neural voices).
    Accepts JSON {text, lang}, returns MP3 audio bytes.
    """
    from django.http import HttpResponse
    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        lang = data.get('lang', 'en-IN')
        rate = data.get('rate', '+10%')   # speed adjustment

        if not text:
            return JsonResponse({'error': 'No text provided'}, status=400)

        # Cap at 800 chars to keep latency reasonable
        if len(text) > 800:
            text = text[:800] + '…'

        voice = _EDGE_VOICES.get(lang, 'en-IN-NeerjaNeural')
        audio_bytes = _edge_tts_synthesize(text, voice, rate=rate)

        if not audio_bytes:
            return JsonResponse({'error': 'TTS produced no audio'}, status=500)

        return HttpResponse(audio_bytes, content_type='audio/mpeg')

    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=500)