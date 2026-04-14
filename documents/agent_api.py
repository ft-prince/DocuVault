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

# Maps change_type values to human-readable change_note prefixes.
# The _infer_event() helper in views.py parses these back out for the
# version history display on the document detail page.
_CHANGE_NOTE_MAP = {
    'initial_sync': 'Initial sync via Desktop Agent',
    'created':      'Auto-synced (created)',
    'modified':     'Auto-synced (modified)',
}


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
        watch_path  — the local folder path being watched
        change_note — description of what changed (optional)
        change_type — 'created' | 'modified' | 'initial_sync'
        category    — category name (optional)
        folder_id   — workspace folder ID to sync into (optional)

    Dedup logic (in priority order):
      1. Match by [agent:<normalised_file_path>] tag in description  (existing records)
      2. Match by title + owner + same folder                        (fallback)
      Never creates a second Document for the same physical file.

    Version logic:
      - initial_sync  → skip entirely if file content (MD5) is unchanged
      - created       → always create v1 (new file appeared)
      - modified      → create new version only if MD5 differs from current
    """
    import hashlib

    user = _get_agent_user(request)
    if user is None:
        return _json_error('Invalid or missing token', status=401)

    if 'file' not in request.FILES:
        return _json_error('file field is required')

    uploaded_file = request.FILES['file']

    # ── Read POST fields ──────────────────────────────────────
    file_path     = request.POST.get('file_path', '').strip()
    watch_path    = request.POST.get('watch_path', '').strip()
    title         = request.POST.get('title', '').strip() or os.path.splitext(uploaded_file.name)[0]
    category_name = request.POST.get('category', '').strip()
    folder_id_str = request.POST.get('folder_id', '').strip()

    change_type = request.POST.get('change_type', 'modified').strip()
    if change_type not in _CHANGE_NOTE_MAP:
        change_type = 'modified'

    type_prefix = _CHANGE_NOTE_MAP[change_type]
    change_note = f"{type_prefix}: {uploaded_file.name}"

    # ── Normalise the dedup key (always forward slashes) ─────
    # This is stored in description AND used for lookup — consistent format
    # prevents the "already exists but not found" duplicate-create bug.
    raw_key  = file_path or watch_path
    dedup_key = raw_key.replace('\\', '/').strip() if raw_key else ''

    # ── Helpers ───────────────────────────────────────────────
    def _md5_upload(file_obj):
        h = hashlib.md5()
        for chunk in file_obj.chunks():
            h.update(chunk)
        file_obj.seek(0)
        return h.hexdigest()

    def _md5_disk(path):
        try:
            with open(path, 'rb') as fh:
                return hashlib.md5(fh.read()).hexdigest()
        except Exception:
            return None

    # ── Resolve category ──────────────────────────────────────
    category = None
    if category_name:
        category, _ = Category.objects.get_or_create(name=category_name)

    # ── Resolve workspace folder ──────────────────────────────
    target_folder = None
    if folder_id_str:
        try:
            from .models import Folder as _Folder
            target_folder = _Folder.objects.get(id=int(folder_id_str), owner=user)
        except Exception:
            pass

    # ── Dedup lookup ─────────────────────────────────────────
    # Strategy: try every reasonable variant of the path so old records
    # (which may have been stored with backslashes) are still found.
    def _find_existing():
        variants = list({dedup_key, raw_key})   # forward-slash + original
        variants = [v for v in variants if v]

        for v in variants:
            doc = Document.objects.filter(
                owner=user,
                is_deleted=False,
                description__contains=f'[agent:{v}]'
            ).first()
            if doc:
                return doc

        # Fallback: match by title + owner + folder (catches records created
        # before the [agent:…] tag was introduced)
        qs = Document.objects.filter(owner=user, is_deleted=False, title=title)
        if target_folder is not None:
            qs = qs.filter(folder=target_folder)
        return qs.first()

    existing = _find_existing()

    if existing:
        # ── Existing document — maybe create a new version ────
        document = existing
        new_hash = _md5_upload(uploaded_file)
        cur_hash = _md5_disk(document.file.path) if document.file else None

        if new_hash and cur_hash and new_hash == cur_hash:
            # File unchanged — skip silently (covers initial_sync restarts
            # and spurious OS modify events)
            return _json_ok({
                'document_id': document.pk,
                'version':     document.version,
                'title':       document.title,
                'action':      'skipped_no_change',
                'folder_id':   document.folder_id,
                'folder_name': document.folder.name if document.folder else None,
            })

        # Content has changed — save a new version
        # Always use 'modified' note for updates regardless of what change_type
        # the agent sent — on_created can fire for files that already exist
        # if the agent restarts or the file is moved then modified.
        update_note = f"{_CHANGE_NOTE_MAP['modified']}: {uploaded_file.name}"
        new_version        = document.version + 1
        document.version   = new_version
        document.file      = uploaded_file
        document.file_size = uploaded_file.size
        document.file_type = (
            uploaded_file.content_type
            or mimetypes.guess_type(uploaded_file.name)[0]
            or 'application/octet-stream'
        )
        document.updated_at = timezone.now()
        if target_folder is not None:
            document.folder = target_folder
        document.save()

        DocumentVersion.objects.get_or_create(
            document=document,
            version_number=new_version,
            defaults={
                'file':        document.file,
                'file_size':   document.file_size,
                'uploaded_by': user,
                'change_note': update_note,
            }
        )

        # Reset RAG embedding so new content gets re-indexed
        try:
            from .models import DocumentEmbedding
            emb, _ = DocumentEmbedding.objects.get_or_create(document=document)
            emb.is_indexed    = False
            emb.index_status  = 'pending'
            emb.error_message = ''
            emb.save(update_fields=['is_indexed', 'index_status', 'error_message'])
        except Exception:
            pass

        ActivityLog.objects.create(
            user=user,
            document=document,
            action='edit',
            description=f"Desktop Agent auto-synced v{new_version}: {document.title}",
            ip_address='127.0.0.1'
        )
        _notify_watchers(
            document, user,
            f"Document '{document.title}' updated to v{new_version} by Desktop Agent"
        )
        _increment_sync_done(watch_path, change_type)

        return _json_ok({
            'document_id': document.pk,
            'version':     new_version,
            'title':       document.title,
            'action':      'updated',
            'folder_id':   document.folder_id,
            'folder_name': document.folder.name if document.folder else None,
        })

    else:
        # ── Brand-new document ────────────────────────────────
        description = (
            f'[agent:{dedup_key}]\nAuto-synced document.'
            if dedup_key else
            'Auto-synced by Desktop Agent.'
        )
        v1_note = (
            'Initial sync via Desktop Agent'
            if change_type == 'initial_sync'
            else f'Auto-synced (created): {uploaded_file.name}'
        )

        document = Document.objects.create(
            owner=user,
            title=title,
            description=description,
            file=uploaded_file,
            file_size=uploaded_file.size,
            file_type=(
                uploaded_file.content_type
                or mimetypes.guess_type(uploaded_file.name)[0]
                or 'application/octet-stream'
            ),
            version=1,
            access_level='private',
            category=category,
            folder=target_folder,
        )

        DocumentVersion.objects.create(
            document=document,
            version_number=1,
            file=document.file,
            file_size=document.file_size,
            uploaded_by=user,
            change_note=v1_note,
        )

        ActivityLog.objects.create(
            user=user,
            document=document,
            action='create',
            description=f"Desktop Agent created: {document.title}",
            ip_address='127.0.0.1'
        )
        _increment_sync_done(watch_path, change_type)

        return _json_ok({
            'document_id': document.pk,
            'version':     1,
            'title':       document.title,
            'action':      'created',
            'folder_id':   document.folder_id,
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
                'id':               log.pk,
                'action':           log.action,
                'document_id':      log.document.pk,
                'document_title':   log.document.title,
                'document_version': log.document.version,
                'changed_by':       log.user.username,
                'timestamp':        log.created_at.isoformat(),
                'description':      log.description,
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
        'status':      'online',
        'server_time': timezone.now().isoformat(),
        'user':        user.username,
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
        online    = bool(last_used and (timezone.now() - last_used).total_seconds() <= 120)
        return _json_ok({
            'online':   online,
            'last_seen': last_used.isoformat() if last_used else None,
            'username':  request.user.username,
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
    if document.owner != sender:
        Notification.objects.create(
            recipient=document.owner,
            sender=sender,
            notification_type='document_updated',
            title='Document Updated',
            message=message,
            document=document,
        )


def _increment_sync_done(watch_path: str, change_type: str):
    """
    Increment the in-memory sync progress counter after each successful upload
    so the frontend /agent/sync/status/ polling shows a live progress bar
    during initial_sync runs.

    Only increments for initial_sync events — live watchdog events don't need
    a progress bar.
    """
    if change_type != 'initial_sync' or not watch_path:
        return
    try:
        from .views import _SYNC_STATE, _SYNC_STATE_LOCK
        with _SYNC_STATE_LOCK:
            state = _SYNC_STATE.get(watch_path)
            if state and state.get('status') == 'running':
                state['done'] = state.get('done', 0) + 1
    except Exception:
        pass  # non-critical — never let this break an upload


# ─────────────────────────────────────────────────────────────
# Utility: fix legacy backslash dedup keys (run once from shell)
# ─────────────────────────────────────────────────────────────

def fix_agent_description_paths():
    """
    One-time fix for existing documents whose description contains
    [agent:C:\\path\\to\\file] (backslashes).  Normalises them to
    [agent:C:/path/to/file] so the dedup lookup always finds them.

    Run from Django shell:
        from documents.agent_api import fix_agent_description_paths
        fix_agent_description_paths()
    """
    fixed = 0
    for doc in Document.objects.filter(description__contains='[agent:'):
        if '\\' in doc.description:
            doc.description = doc.description.replace('\\', '/')
            doc.save(update_fields=['description'])
            fixed += 1
    print(f"Fixed {fixed} document(s).")
    return fixed