"""
DocuVault Desktop Agent API
============================
JSON endpoints consumed exclusively by the Desktop Agent.
Authentication: Authorization: Token <hex-token>
No session cookies or CSRF tokens required.
"""

import os
import json
import mimetypes
from datetime import timedelta

from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import (
    User, Document, DocumentVersion, ActivityLog,
    AgentToken, Notification, Category,
)


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _get_agent_user(request):
    """Extract and validate Bearer token from Authorization header."""
    auth = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth.startswith('Token '):
        return None
    token_value = auth[6:].strip()
    user, _ = AgentToken.authenticate(token_value)
    return user


def _json_error(message, status=400):
    return JsonResponse({'ok': False, 'error': message}, status=status)


def _json_ok(data=None, status=200):
    payload = {'ok': True}
    if data:
        payload.update(data)
    return JsonResponse(payload, status=status)


# ─────────────────────────────────────────────────────────────
# 1. Auth — issue or retrieve token
# ─────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def agent_auth_view(request):
    """
    POST /agent/auth/
    Body (JSON or form): {username, password}
    Returns: {token, user_id, username}
    """
    try:
        if request.content_type and 'application/json' in request.content_type:
            body = json.loads(request.body)
        else:
            body = request.POST
        username = body.get('username', '').strip()
        password = body.get('password', '').strip()
    except Exception:
        return _json_error('Invalid request body')

    if not username or not password:
        return _json_error('username and password are required')

    user = authenticate(request, username=username, password=password)
    if user is None:
        return _json_error('Invalid credentials', status=401)

    token = AgentToken.get_or_create_for_user(user)
    return _json_ok({
        'token': token,
        'user_id': user.pk,
        'username': user.username,
    })


# ─────────────────────────────────────────────────────────────
# 2. Upload — create or update document from watched folder
# ─────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def agent_upload_view(request):
    """
    POST /agent/upload/
    Auth: Authorization: Token <token>
    Multipart body:
        file        — the file to upload
        title       — document title (optional; defaults to filename)
        file_path   — full local path of the file (primary dedup key)
        watch_path  — the local folder path being watched (legacy / fallback)
        change_note — description of what changed (optional)
        category    — category name (optional)
        folder_id   — workspace folder ID to sync into (optional)

    Logic:
      - If a Document with the same owner + file_path already exists → new version
      - Otherwise → create new document at version 1
    Returns: {document_id, version, title, action}
    """
    user = _get_agent_user(request)
    if user is None:
        return _json_error('Invalid or missing token', status=401)

    if 'file' not in request.FILES:
        return _json_error('file field is required')

    uploaded_file = request.FILES['file']
    # file_path is the full path of the file on the client machine — used as unique dedup key
    file_path     = request.POST.get('file_path', '').strip()
    watch_path    = request.POST.get('watch_path', '').strip()
    title         = request.POST.get('title', '').strip() or os.path.splitext(uploaded_file.name)[0]
    change_note   = request.POST.get('change_note', 'Auto-synced by Desktop Agent').strip()
    category_name = request.POST.get('category', '').strip()
    folder_id_str = request.POST.get('folder_id', '').strip()

    # Resolve category
    category = None
    if category_name:
        category, _ = Category.objects.get_or_create(name=category_name)

    # Resolve workspace folder (optional — agent sends folder_id from config)
    target_folder = None
    if folder_id_str:
        try:
            from .models import Folder as _Folder
            target_folder = _Folder.objects.get(id=int(folder_id_str), owner=user)
        except Exception:
            pass  # folder not found or invalid — just leave unfiled

    # Determine if this is an update or create.
    # Dedup key: file_path (full path) takes priority over watch_path (folder).
    # This ensures each file gets its own Document — not one document per folder.
    existing = None
    dedup_key = file_path or watch_path
    if dedup_key:
        existing = Document.objects.filter(
            owner=user,
            is_deleted=False,
            description__startswith=f'[agent:{dedup_key}]'
        ).first()

    if existing:
        # ── New version of an existing document ──────────────────
        document = existing
        old_version = document.version
        document.version += 1
        document.file = uploaded_file
        document.file_size = uploaded_file.size
        document.file_type = uploaded_file.content_type or mimetypes.guess_type(uploaded_file.name)[0] or 'application/octet-stream'
        document.updated_at = timezone.now()
        # Move to the configured folder if one is specified
        if target_folder is not None:
            document.folder = target_folder
        document.save()

        DocumentVersion.objects.get_or_create(
            document=document,
            version_number=document.version,
            defaults={
                'file': document.file,
                'file_size': document.file_size,
                'uploaded_by': user,
                'change_note': change_note,
            }
        )

        ActivityLog.objects.create(
            user=user,
            document=document,
            action='edit',
            description=f"Desktop Agent auto-synced v{document.version}: {document.title}",
            ip_address='127.0.0.1'
        )

        # Notify document owner if shared
        _notify_watchers(document, user, f"Document '{document.title}' was updated to v{document.version} by Desktop Agent")

        return _json_ok({
            'document_id': document.pk,
            'version': document.version,
            'title': document.title,
            'action': 'updated',
            'folder_id': document.folder_id,
            'folder_name': document.folder.name if document.folder else None,
        })

    else:
        # ── Brand-new document ────────────────────────────────────
        description = f'[agent:{dedup_key}]\nAuto-synced document.' if dedup_key else 'Auto-synced by Desktop Agent.'

        document = Document.objects.create(
            owner=user,
            title=title,
            description=description,
            file=uploaded_file,
            file_size=uploaded_file.size,
            file_type=uploaded_file.content_type or mimetypes.guess_type(uploaded_file.name)[0] or 'application/octet-stream',
            version=1,
            access_level='private',
            category=category,
            folder=target_folder,       # None = unfiled; set if agent configured a folder
        )

        DocumentVersion.objects.create(
            document=document,
            version_number=1,
            file=document.file,
            file_size=document.file_size,
            uploaded_by=user,
            change_note='Initial version — synced by Desktop Agent',
        )

        ActivityLog.objects.create(
            user=user,
            document=document,
            action='create',
            description=f"Desktop Agent created: {document.title}",
            ip_address='127.0.0.1'
        )

        return _json_ok({
            'document_id': document.pk,
            'version': 1,
            'title': document.title,
            'action': 'created',
            'folder_id': document.folder_id,
            'folder_name': document.folder.name if document.folder else None,
        }, status=201)


# ─────────────────────────────────────────────────────────────
# 3. Events — recent version changes for real-time dashboard
# ─────────────────────────────────────────────────────────────

@require_http_methods(['GET'])
def agent_events_view(request):
    """
    GET /agent/events/?since=<ISO-timestamp>
    Auth: Authorization: Token <token>  — OR — session cookie (dashboard polling)

    Returns the last 50 document edit/create events visible to the user,
    optionally filtered to events after `since`.
    Used by both the Desktop Agent and the dashboard's auto-refresh JS.
    """
    # Accept both token auth (agent) and session auth (dashboard)
    if request.user.is_authenticated:
        user = request.user
    else:
        user = _get_agent_user(request)
        if user is None:
            return _json_error('Authentication required', status=401)

    since_str = request.GET.get('since')
    qs = ActivityLog.objects.filter(
        action__in=['create', 'edit'],
    ).select_related('user', 'document').order_by('-created_at')

    if since_str:
        try:
            from dateutil import parser as dtparser
            since_dt = dtparser.isoparse(since_str)
            if since_dt.tzinfo is None:
                from django.utils.timezone import make_aware
                since_dt = make_aware(since_dt)
            qs = qs.filter(created_at__gt=since_dt)
        except Exception:
            pass

    qs = qs[:50]

    events = []
    for log in qs:
        if log.document and log.document.can_view(user):
            events.append({
                'id': log.pk,
                'action': log.action,
                'document_id': log.document.pk,
                'document_title': log.document.title,
                'document_version': log.document.version,
                'changed_by': log.user.username,
                'timestamp': log.created_at.isoformat(),
                'description': log.description,
            })

    return _json_ok({'events': events, 'count': len(events)})


# ─────────────────────────────────────────────────────────────
# 4. Heartbeat — agent confirms it is alive
# ─────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def agent_heartbeat_view(request):
    """
    POST /agent/heartbeat/
    Auth: Authorization: Token <token>
    Returns: {status, server_time, user}
    """
    user = _get_agent_user(request)
    if user is None:
        return _json_error('Invalid or missing token', status=401)

    return _json_ok({
        'status': 'online',
        'server_time': timezone.now().isoformat(),
        'user': user.username,
    })


@require_http_methods(['GET'])
def agent_status_view(request):
    """
    GET /agent/status/
    Session-authenticated (dashboard uses this).
    Returns whether the current user's Desktop Agent last checked in recently.
    "online" = heartbeat within last 2 minutes.
    """
    if not request.user.is_authenticated:
        return _json_error('Login required', status=401)

    try:
        token_obj = AgentToken.objects.get(user=request.user, is_active=True)
        last_used = token_obj.last_used
        if last_used is None:
            online = False
        else:
            age_seconds = (timezone.now() - last_used).total_seconds()
            online = age_seconds <= 120   # 2-minute window
        return _json_ok({
            'online': online,
            'last_seen': last_used.isoformat() if last_used else None,
            'username': request.user.username,
        })
    except AgentToken.DoesNotExist:
        return _json_ok({'online': False, 'last_seen': None, 'username': request.user.username})


# ─────────────────────────────────────────────────────────────
# 5. Token reset — revoke + regenerate token
# ─────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def agent_token_reset_view(request):
    """
    POST /agent/token/reset/
    Auth: Authorization: Token <old-token>
    Generates a new token and invalidates the old one.
    """
    import secrets
    user = _get_agent_user(request)
    if user is None:
        return _json_error('Invalid or missing token', status=401)

    token_obj = AgentToken.objects.get(user=user)
    token_obj.token = secrets.token_hex(32)
    token_obj.save(update_fields=['token'])

    return _json_ok({'token': token_obj.token})


# ─────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────

def _notify_watchers(document, sender, message):
    """Notify users who can view the document that it changed."""
    # For now: only notify the document owner if the agent is a different user
    if document.owner != sender:
        Notification.objects.create(
            recipient=document.owner,
            sender=sender,
            notification_type='document_updated',
            title='Document Updated',
            message=message,
            document=document,
        )
