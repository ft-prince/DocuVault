import os 

from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse, FileResponse, Http404
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.db import transaction
import json
import mimetypes

from .models import (
    User, Role, Document, Category, Tag, DocumentVersion,
    DocumentComment, SharedLink, Favorite, ActivityLog, Notification, Folder
)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .forms import (
    UserRegistrationForm, UserLoginForm, DocumentForm, CategoryForm,
    RoleForm, UserProfileForm, CommentForm, SharedLinkForm
)


# ============================================================
# AUTHENTICATION VIEWS
# ============================================================

def register_view(request):
    """User registration"""
    if request.user.is_authenticated:
        return redirect('workspace')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = 'user'  # Default to regular user
            user.save()
            
            # Assign default role if exists
            default_role = Role.objects.filter(is_default=True).first()
            if default_role:
                user.role = default_role
                user.save()
            
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('workspace')
    else:
        form = UserRegistrationForm()
    
    
    return render(request, 'documents/auth/register.html', {'form': form})


def login_view(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('workspace')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect(request.GET.get('next', 'workspace'))
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'documents/auth/login.html', {'form': form})


@login_required
def logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('home')


# ============================================================
# DASHBOARD AND HOME
# ============================================================

def home_view(request):
    """Public home page"""
    public_documents = Document.objects.filter(
        access_level='public',
        is_deleted=False
    ).select_related('owner', 'category').prefetch_related('tags')[:12]
    
    categories = Category.objects.annotate(
        doc_count=Count('documents')
    ).filter(doc_count__gt=0)[:8]
    
    context = {
        'public_documents': public_documents,
        'categories': categories,
    }
    return render(request, 'documents/home.html', context)


@login_required
def dashboard_view(request):
    """User dashboard"""
    user = request.user
    
    # Get user's documents
    my_documents = Document.objects.filter(
        owner=user,
        is_deleted=False
    ).select_related('category')[:5]
    
    # Get recently viewed documents
    recent_views = ActivityLog.objects.filter(
        user=user,
        action='view'
    ).select_related('document').order_by('-created_at')[:5]
    
    # Get shared documents
    shared_documents = user.shared_documents.filter(
        is_deleted=False
    ).select_related('owner', 'category')[:5]
    
    # Get favorites
    favorites = Favorite.objects.filter(
        user=user
    ).select_related('document', 'document__owner')[:5]
    
    # Get unread notifications
    unread_notifications = user.notifications.filter(is_read=False)[:5]
    
    # Statistics
    stats = {
        'total_documents': my_documents.count(),
        'shared_with_me': shared_documents.count(),
        'favorites': favorites.count(),
        'unread_notifications': unread_notifications.count(),
    }
    
    context = {
        'my_documents': my_documents,
        'recent_views': recent_views,
        'shared_documents': shared_documents,
        'favorites': favorites,
        'unread_notifications': unread_notifications,
        'stats': stats,
    }
    return render(request, 'documents/dashboard.html', context)


# ============================================================
# DOCUMENT VIEWS
# ============================================================

@login_required
def document_list_view(request):
    """List all accessible documents"""
    user = request.user
    
    # Base queryset
    documents = Document.objects.filter(is_deleted=False).select_related(
        'owner', 'category'
    ).prefetch_related('tags')
    
    # Filter by access permissions
    if not user.is_admin():
        documents = documents.filter(
            Q(owner=user) |  # Own documents
            Q(access_level='public') |  # Public documents
            Q(access_level='role', required_role_level__lte=user.get_role_level()) |  # Role-based
            Q(access_level='custom', shared_with=user)  # Shared with user
        ).distinct()
    
    # Search and filters
    search_query = request.GET.get('q', '')
    if search_query:
        documents = documents.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__name__icontains=search_query)
        ).distinct()
    
    category_id = request.GET.get('category')
    if category_id:
        documents = documents.filter(category_id=category_id)
    
    tag_id = request.GET.get('tag')
    if tag_id:
        documents = documents.filter(tags__id=tag_id)
    
    access_level = request.GET.get('access_level')
    if access_level:
        documents = documents.filter(access_level=access_level)
    
    # Sorting
    sort_by = request.GET.get('sort', '-updated_at')
    documents = documents.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(documents, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'categories': Category.objects.all(),
        'tags': Tag.objects.all(),
    }
    return render(request, 'documents/document_list.html', context)


@login_required
def document_detail_view(request, pk):
    """View document details"""
    document = get_object_or_404(Document, pk=pk, is_deleted=False)
    
    # Check permissions
    if not document.can_view(request.user):
        raise PermissionDenied("You don't have permission to view this document.")
    
    # Log view activity
    ActivityLog.objects.create(
        user=request.user,
        document=document,
        action='view',
        description=f"Viewed document: {document.title}",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    document.increment_views()
    
    # Get comments
    comments = document.comments.filter(parent=None).select_related('user').prefetch_related('replies')
    
    # Get ALL versions — full history like GitHub
    versions = document.versions.select_related('uploaded_by').order_by('-version_number')
    
    # Check if favorited
    is_favorited = Favorite.objects.filter(user=request.user, document=document).exists()
    
    # Get recent activity
    recent_activity = document.activity_logs.select_related('user')[:10]
    
    # Get indexing status
    try:
        from .models import DocumentEmbedding
        embedding = document.embedding
    except Exception:
        embedding = None

    context = {
        'document': document,
        'comments': comments,
        'versions': versions,
        'is_favorited': is_favorited,
        'recent_activity': recent_activity,
        'can_edit': document.can_edit(request.user),
        'can_delete': document.can_delete(request.user),
        'embedding': embedding,
    }
    return render(request, 'documents/document_detail.html', context)


@login_required
def document_create_view(request):
    """Create a new document"""
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            document = form.save(commit=False)
            document.owner = request.user
            
            # Get file info
            if 'file' in request.FILES:
                uploaded_file = request.FILES['file']
                document.file_size = uploaded_file.size
                document.file_type = uploaded_file.content_type
            
            # Auto-assign to folder if ?folder= was in the create URL
            folder_id = request.POST.get('_folder_id') or request.GET.get('folder')
            if folder_id:
                try:
                    document.folder = Folder.objects.get(id=folder_id, owner=request.user)
                except Folder.DoesNotExist:
                    pass

            document.save()
            form.save_m2m()  # Save many-to-many relationships (tags)

            # Create version 1
            if document.file:
                DocumentVersion.objects.create(
                    document=document,
                    version_number=1,
                    file=document.file,
                    file_size=document.file_size,
                    uploaded_by=request.user,
                    change_note="Initial version"
                )

            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                document=document,
                action='create',
                description=f"Created document: {document.title}",
                ip_address=request.META.get('REMOTE_ADDR')
            )

            messages.success(request, 'Document created successfully!')
            if document.folder:
                from django.urls import reverse as _rev
                return redirect(_rev('workspace') + f'?folder={document.folder_id}')
            return redirect('workspace')
    else:
        form = DocumentForm(user=request.user)

    folder_id = request.GET.get('folder')
    pre_folder = None
    if folder_id:
        try:
            pre_folder = Folder.objects.get(id=folder_id, owner=request.user)
        except Folder.DoesNotExist:
            pass

    return render(request, 'documents/document_form.html', {
        'form': form, 'action': 'Create', 'pre_folder': pre_folder,
    })


@login_required
def document_edit_view(request, pk):
    """Edit a document"""
    document = get_object_or_404(Document, pk=pk, is_deleted=False)

    # Check permissions
    if not document.can_edit(request.user):
        raise PermissionDenied("You don't have permission to edit this document.")

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=document, user=request.user)
        if form.is_valid():
            # Capture values BEFORE form mutates the instance
            old_file = document.file
            old_file_size = document.file_size
            old_version_number = document.version

            document = form.save(commit=False)

            if 'file' in request.FILES and request.FILES['file']:
                uploaded_file = request.FILES['file']

                # Increment version first
                new_version_number = old_version_number + 1
                document.file_size = uploaded_file.size
                document.file_type = uploaded_file.content_type
                document.version = new_version_number

                # Save document FIRST so owner FK is resolvable in upload path
                document.save()
                form.save_m2m()

                # Archive the OLD file as a version snapshot (if not already recorded)
                DocumentVersion.objects.get_or_create(
                    document=document,
                    version_number=old_version_number,
                    defaults={
                        'file': old_file,
                        'file_size': old_file_size,
                        'uploaded_by': request.user,
                        'change_note': f'Version {old_version_number}',
                    }
                )

                # Create a version record for the NEW version
                change_note_new = request.POST.get('change_note', '').strip() or f'Version {new_version_number}'
                DocumentVersion.objects.get_or_create(
                    document=document,
                    version_number=new_version_number,
                    defaults={
                        'file': document.file,
                        'file_size': document.file_size,
                        'uploaded_by': request.user,
                        'change_note': change_note_new,
                    }
                )
            else:
                document.save()
                form.save_m2m()

            # Reset embedding so auto-indexing re-runs on file replace
            if 'file' in request.FILES and request.FILES['file']:
                try:
                    from .models import DocumentEmbedding
                    emb, _ = DocumentEmbedding.objects.get_or_create(document=document)
                    emb.is_indexed = False
                    emb.index_status = 'pending'
                    emb.error_message = ''
                    emb.save(update_fields=['is_indexed', 'index_status', 'error_message'])
                except Exception:
                    pass

            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                document=document,
                action='edit',
                description=f"Edited document: {document.title}",
                ip_address=request.META.get('REMOTE_ADDR')
            )

            messages.success(request, 'Document updated successfully!')
            return redirect('document_detail', pk=document.pk)
    else:
        form = DocumentForm(instance=document, user=request.user)

    return render(request, 'documents/document_form.html', {
        'form': form,
        'document': document,
        'action': 'Edit'
    })


@login_required
def document_delete_view(request, pk):
    """Delete a document (soft delete)"""
    document = get_object_or_404(Document, pk=pk, is_deleted=False)
    
    # Check permissions
    if not document.can_delete(request.user):
        raise PermissionDenied("You don't have permission to delete this document.")
    
    if request.method == 'POST':
        document.is_deleted = True
        document.deleted_at = timezone.now()
        document.save()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            document=document,
            action='delete',
            description=f"Deleted document: {document.title}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, 'Document deleted successfully!')
        return redirect('document_list')
    
    return render(request, 'documents/document_confirm_delete.html', {'document': document})


import os
from django.utils.encoding import escape_uri_path

@login_required
def document_download_view(request, pk):
    """Download a document"""
    document = get_object_or_404(Document, pk=pk, is_deleted=False)
    
    # Check permissions
    if not document.can_view(request.user):
        raise PermissionDenied("You don't have permission to download this document.")
    
    if not document.allow_download:
        messages.error(request, 'Downloads are not allowed for this document.')
        return redirect('document_detail', pk=document.pk)
    
    # Log download activity
    ActivityLog.objects.create(
        user=request.user,
        document=document,
        action='download',
        description=f"Downloaded document: {document.title}",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    document.increment_downloads()
    
    # Serve file
    file_path = document.file.path
    if not os.path.exists(file_path):
        raise Http404("File not found.")
    
    # Get the original filename from the file field
    original_filename = os.path.basename(document.file.name)
    
    response = FileResponse(open(file_path, 'rb'))
    response['Content-Type'] = document.file_type or 'application/octet-stream'
    response['Content-Disposition'] = f'attachment; filename="{escape_uri_path(original_filename)}"'
    
    return response


@login_required
def version_download_view(request, doc_pk, version_pk):
    """Download a specific historical version of a document"""
    document = get_object_or_404(Document, pk=doc_pk, is_deleted=False)

    if not document.can_view(request.user):
        raise PermissionDenied("You don't have permission to access this document.")

    if not document.allow_download:
        messages.error(request, 'Downloads are not allowed for this document.')
        return redirect('document_detail', pk=document.pk)

    version = get_object_or_404(DocumentVersion, pk=version_pk, document=document)

    file_path = version.file.path
    if not os.path.exists(file_path):
        raise Http404("Version file not found.")

    # Build a descriptive filename: title_v2.docx
    ext = os.path.splitext(version.file.name)[1]
    safe_title = document.title.replace(' ', '_')
    download_name = f"{safe_title}_v{version.version_number}{ext}"

    ActivityLog.objects.create(
        user=request.user,
        document=document,
        action='download',
        description=f"Downloaded version {version.version_number} of: {document.title}",
        ip_address=request.META.get('REMOTE_ADDR')
    )

    response = FileResponse(open(file_path, 'rb'))
    response['Content-Type'] = document.file_type or 'application/octet-stream'
    response['Content-Disposition'] = f'attachment; filename="{escape_uri_path(download_name)}"'
    return response


@login_required
@require_POST
def version_restore_view(request, doc_pk, version_pk):
    """Restore a previous version — creates a new version from the old file."""
    document = get_object_or_404(Document, pk=doc_pk, is_deleted=False)
    if not document.can_edit(request.user):
        raise PermissionDenied

    old_ver = get_object_or_404(DocumentVersion, pk=version_pk, document=document)
    if not os.path.exists(old_ver.file.path):
        messages.error(request, 'Version file not found on disk.')
        return redirect('document_detail', pk=document.pk)

    import shutil
    from django.core.files import File

    # New version number = current doc version + 1
    new_ver_num = document.version + 1

    # Copy the old file to a new path so both versions stay on disk
    old_path   = old_ver.file.path
    old_ext    = os.path.splitext(old_path)[1]
    import uuid as _uuid
    new_name   = f'{_uuid.uuid4()}{old_ext}'
    new_dir    = os.path.dirname(old_path)
    new_path   = os.path.join(new_dir, new_name)
    shutil.copy2(old_path, new_path)

    # Archive current document file as the previous version first
    if document.file and os.path.exists(document.file.path):
        cur_ext  = os.path.splitext(document.file.path)[1]
        cur_name = f'{_uuid.uuid4()}{cur_ext}'
        cur_path = os.path.join(new_dir, cur_name)
        shutil.copy2(document.file.path, cur_path)
        DocumentVersion.objects.get_or_create(
            document=document,
            version_number=document.version,
            defaults={
                'uploaded_by': request.user,
                'file':        f'documents/{document.owner.id}/{cur_name}',
                'file_size':   document.file_size or 0,
                'change_note': f'Auto-archived before restore to v{old_ver.version_number}',
            }
        )

    # Point document.file to the restored copy
    with open(new_path, 'rb') as fh:
        document.file.save(new_name, File(fh), save=False)

    document.version   = new_ver_num
    document.file_size = old_ver.file_size
    document.save()

    # Create a version record for the restore
    DocumentVersion.objects.create(
        document=document,
        version_number=new_ver_num,
        uploaded_by=request.user,
        file=document.file,
        file_size=old_ver.file_size,
        change_note=f'Restored from v{old_ver.version_number}',
    )

    ActivityLog.objects.create(
        user=request.user,
        document=document,
        action='edit',
        description=f'Restored document to v{old_ver.version_number} → new v{new_ver_num}',
        ip_address=request.META.get('REMOTE_ADDR'),
    )

    messages.success(request, f'Document restored to v{old_ver.version_number} (now v{new_ver_num}).')
    return redirect('document_detail', pk=document.pk)


# ============================================================
# COMMENT VIEWS
# ============================================================

@login_required
def comment_create_view(request, document_pk):
    """Add a comment to a document"""
    document = get_object_or_404(Document, pk=document_pk, is_deleted=False)
    
    if not document.can_view(request.user) or not document.allow_comments:
        raise PermissionDenied()
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        parent_id = request.POST.get('parent_id')
        
        if content:
            comment = DocumentComment.objects.create(
                document=document,
                user=request.user,
                content=content,
                parent_id=parent_id if parent_id else None
            )
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                document=document,
                action='comment',
                description=f"Commented on: {document.title}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            # Notify document owner
            if request.user != document.owner:
                Notification.objects.create(
                    recipient=document.owner,
                    sender=request.user,
                    notification_type='comment_added',
                    title='New Comment',
                    message=f"{request.user.username} commented on your document: {document.title}",
                    document=document
                )
            
            messages.success(request, 'Comment added successfully!')
        
        return redirect('document_detail', pk=document_pk)


@login_required
def comment_delete_view(request, pk):
    """Delete a comment"""
    comment = get_object_or_404(DocumentComment, pk=pk)
    
    if request.user != comment.user and not request.user.is_admin():
        raise PermissionDenied()
    
    if request.method == 'POST':
        document_pk = comment.document.pk
        comment.delete()
        messages.success(request, 'Comment deleted successfully!')
        return redirect('document_detail', pk=document_pk)


# ============================================================
# FAVORITE VIEWS
# ============================================================

@login_required
def favorite_toggle_view(request, document_pk):
    """Toggle favorite status for a document"""
    document = get_object_or_404(Document, pk=document_pk, is_deleted=False)
    
    if not document.can_view(request.user):
        raise PermissionDenied()
    
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        document=document
    )
    
    if not created:
        favorite.delete()
        messages.success(request, 'Removed from favorites.')
        action = 'removed'
    else:
        ActivityLog.objects.create(
            user=request.user,
            document=document,
            action='favorite',
            description=f"Favorited: {document.title}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        messages.success(request, 'Added to favorites!')
        action = 'added'
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'action': action})
    
    return redirect('document_detail', pk=document_pk)


@login_required
def favorites_list_view(request):
    """List user's favorite documents"""
    favorites = Favorite.objects.filter(
        user=request.user
    ).select_related('document', 'document__owner', 'document__category')
    
    paginator = Paginator(favorites, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'documents/favorites_list.html', {'page_obj': page_obj})


# ============================================================
# SHARED LINK VIEWS
# ============================================================

@login_required
def shared_link_create_view(request, document_pk):
    """Create a shareable link for a document"""
    document = get_object_or_404(Document, pk=document_pk, is_deleted=False)
    
    if not document.can_edit(request.user):
        raise PermissionDenied()
    
    created_link = None
    if request.method == 'POST':
        form = SharedLinkForm(request.POST)
        if form.is_valid():
            link = form.save(commit=False)
            link.document = document
            link.created_by = request.user
            link.save()
            created_link = link
            form = SharedLinkForm()  # reset form
    else:
        form = SharedLinkForm()

    return render(request, 'documents/shared_link_form.html', {
        'form': form,
        'document': document,
        'created_link': created_link,
    })


def shared_link_access_view(request, token):
    """Access a document via shared link"""
    link = get_object_or_404(SharedLink, token=token)
    
    if not link.is_valid():
        messages.error(request, 'This link has expired or is no longer valid.')
        return redirect('home')
    
    # Check password if required
    if link.password:
        if request.method == 'POST':
            password = request.POST.get('password', '')
            if password != link.password:
                messages.error(request, 'Incorrect password.')
                return render(request, 'documents/shared_link_password.html', {'link': link})
        else:
            return render(request, 'documents/shared_link_password.html', {'link': link})
    
    link.increment_access()
    document = link.document
    
    context = {
        'document': document,
        'link': link,
        'can_download': link.allow_download,
    }
    return render(request, 'documents/shared_link_view.html', context)


# ============================================================
# USER PROFILE VIEWS
# ============================================================

@login_required
def profile_view(request, username=None):
    """View user profile"""
    if username:
        profile_user = get_object_or_404(User, username=username)
    else:
        profile_user = request.user
    
    # Get user's public documents
    documents = Document.objects.filter(
        owner=profile_user,
        access_level='public',
        is_deleted=False
    )[:10]
    
    context = {
        'profile_user': profile_user,
        'documents': documents,
        'is_own_profile': request.user == profile_user,
    }
    return render(request, 'documents/profile.html', context)


@login_required
def profile_edit_view(request):
    """Edit user profile"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'documents/profile_edit.html', {'form': form})


# ============================================================
# ADMIN VIEWS - USER MANAGEMENT
# ============================================================

@login_required
def admin_users_list_view(request):
    """List all users (admin only)"""
    if not request.user.is_admin():
        raise PermissionDenied()
    
    users = User.objects.all().select_related('role').order_by('-created_at')
    
    search_query = request.GET.get('q', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'documents/admin/users_list.html', {
        'page_obj': page_obj,
        'search_query': search_query
    })


@login_required
def admin_user_update_role_view(request, user_id):
    """Update user's role (admin only)"""
    if not request.user.is_admin():
        raise PermissionDenied()
    
    user = get_object_or_404(User, pk=user_id)
    
    if request.method == 'POST':
        role_id = request.POST.get('role_id')
        user_type = request.POST.get('user_type')
        
        if role_id:
            user.role_id = role_id
        if user_type:
            user.user_type = user_type
        
        user.save()
        messages.success(request, f"Updated role for {user.username}")
        return redirect('admin_users_list')
    
    roles = Role.objects.all()
    return render(request, 'documents/admin/user_update_role.html', {
        'user': user,
        'roles': roles
    })


# ============================================================
# ADMIN VIEWS - ROLE MANAGEMENT
# ============================================================

@login_required
def admin_roles_list_view(request):
    """List all roles (admin only)"""
    if not request.user.is_admin():
        raise PermissionDenied()
    
    roles = Role.objects.annotate(user_count=Count('users')).order_by('-level')
    
    return render(request, 'documents/admin/roles_list.html', {'roles': roles})


@login_required
def admin_role_create_view(request):
    """Create a new role (admin only)"""
    if not request.user.is_admin():
        raise PermissionDenied()
    
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Role created successfully!')
            return redirect('admin_roles_list')
    else:
        form = RoleForm()
    
    return render(request, 'documents/admin/role_form.html', {
        'form': form,
        'action': 'Create'
    })


@login_required
def admin_role_edit_view(request, pk):
    """Edit a role (admin only)"""
    if not request.user.is_admin():
        raise PermissionDenied()
    
    role = get_object_or_404(Role, pk=pk)
    
    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            messages.success(request, 'Role updated successfully!')
            return redirect('admin_roles_list')
    else:
        form = RoleForm(instance=role)
    
    return render(request, 'documents/admin/role_form.html', {
        'form': form,
        'role': role,
        'action': 'Edit'
    })


@login_required
def admin_role_delete_view(request, pk):
    """Delete a role (admin only)"""
    if not request.user.is_admin():
        raise PermissionDenied()
    
    role = get_object_or_404(Role, pk=pk)
    
    if role.is_default:
        messages.error(request, 'Cannot delete default roles.')
        return redirect('admin_roles_list')
    
    if request.method == 'POST':
        role_name = role.name
        role.delete()
        messages.success(request, f'Role "{role_name}" deleted successfully!')
        return redirect('admin_roles_list')
    
    return render(request, 'documents/admin/role_confirm_delete.html', {'role': role})


# ============================================================
# CATEGORY VIEWS
# ============================================================

def category_list_view(request):
    """List all categories"""
    categories = Category.objects.annotate(
        doc_count=Count('documents', filter=Q(documents__is_deleted=False))
    )
    
    return render(request, 'documents/category_list.html', {'categories': categories})


@login_required
def category_create_view(request):
    """Create a new category (admin only)"""
    if not request.user.is_admin():
        raise PermissionDenied()
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.created_by = request.user
            category.save()
            messages.success(request, 'Category created successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'documents/category_form.html', {
        'form': form,
        'action': 'Create'
    })


# ============================================================
# NOTIFICATION VIEWS
# ============================================================

@login_required
def notifications_list_view(request):
    """List user notifications"""
    notifications = request.user.notifications.all()
    
    # Mark all as read
    if request.method == 'POST' and request.POST.get('mark_all_read'):
        notifications.update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
        return redirect('notifications_list')
    
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'documents/notifications_list.html', {'page_obj': page_obj})


@login_required
def notification_mark_read_view(request, pk):
    """Mark notification as read"""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    if notification.document:
        return redirect('document_detail', pk=notification.document.pk)
    return redirect('notifications_list')


# ============================================================
# SEARCH VIEWS
# ============================================================

@login_required
def advanced_search_view(request):
    """Advanced search with filters"""
    documents = Document.objects.filter(is_deleted=False).select_related('owner', 'category')
    
    # Apply filters
    query = request.GET.get('q', '')
    if query:
        documents = documents.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(owner__username__icontains=query)
        )
    
    category_id = request.GET.get('category')
    if category_id:
        documents = documents.filter(category_id=category_id)
    
    owner_id = request.GET.get('owner')
    if owner_id:
        documents = documents.filter(owner_id=owner_id)
    
    date_from = request.GET.get('date_from')
    if date_from:
        documents = documents.filter(created_at__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        documents = documents.filter(created_at__lte=date_to)
    
    # Permission filtering
    if not request.user.is_admin():
        documents = documents.filter(
            Q(owner=request.user) |
            Q(access_level='public') |
            Q(access_level='role', required_role_level__lte=request.user.get_role_level()) |
            Q(access_level='custom', shared_with=request.user)
        ).distinct()
    
    # Get unique owners for the dropdown
    from django.contrib.auth import get_user_model
    User = get_user_model()
    owners = User.objects.filter(
        owned_documents__is_deleted=False
    ).distinct().order_by('username')
    
    paginator = Paginator(documents, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'owners': owners,  # Add this
        'query': query,
    }
    return render(request, 'documents/advanced_search.html', context)
# ============================================================
# ACTIVITY LOG VIEWS
# ============================================================

@login_required
def activity_log_view(request):
    """View activity log"""
    if request.user.is_admin():
        activities = ActivityLog.objects.all()
    else:
        activities = ActivityLog.objects.filter(
            Q(user=request.user) | Q(document__owner=request.user)
        )
    
    activities = activities.select_related('user', 'document').order_by('-created_at')
    
    paginator = Paginator(activities, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'documents/activity_log.html', {'page_obj': page_obj})


# ============================================================
# WORKSPACE — folder tree + all user documents
# ============================================================

def _build_folder_tree(folders, docs_by_folder):
    """Return list of dicts ready for template rendering (recursive)."""
    result = []
    for f in folders:
        children = _build_folder_tree(
            list(f.subfolders.all().order_by('name')), docs_by_folder
        )
        result.append({
            'obj':      f,
            'children': children,
            'count':    docs_by_folder.get(f.id, 0),
        })
    return result


@login_required
def workspace_view(request):
    """Two-panel workspace: folder sidebar + document grid."""
    user = request.user
    folder_id = request.GET.get('folder')
    search_q  = request.GET.get('q', '').strip()

    # All user folders, with their subfolders pre-loaded
    root_folders = (
        Folder.objects
        .filter(owner=user, parent=None)
        .prefetch_related('subfolders__subfolders')
        .order_by('name')
    )

    # Count docs per folder for the sidebar badges
    from django.db.models import Count as _Count
    folder_counts = (
        Document.objects
        .filter(owner=user, is_deleted=False, folder__isnull=False)
        .values('folder_id')
        .annotate(n=_Count('id'))
    )
    docs_by_folder = {row['folder_id']: row['n'] for row in folder_counts}

    folder_tree = _build_folder_tree(list(root_folders), docs_by_folder)

    # Current folder context
    current_folder = None
    if folder_id == 'unfiled':
        docs = Document.objects.filter(owner=user, folder=None, is_deleted=False)
        panel_title = 'Unfiled Documents'
    elif folder_id:
        try:
            current_folder = Folder.objects.get(id=folder_id, owner=user)
            docs = Document.objects.filter(owner=user, folder=current_folder, is_deleted=False)
            panel_title = current_folder.name
        except Folder.DoesNotExist:
            docs = Document.objects.filter(owner=user, is_deleted=False)
            panel_title = 'All Documents'
    else:
        docs = Document.objects.filter(owner=user, is_deleted=False)
        panel_title = 'All Documents'

    if search_q:
        docs = docs.filter(Q(title__icontains=search_q) | Q(description__icontains=search_q))

    docs = docs.select_related('folder', 'category').prefetch_related('versions').order_by('-updated_at')

    # Stats
    total_docs    = Document.objects.filter(owner=user, is_deleted=False).count()
    total_folders = Folder.objects.filter(owner=user).count()
    total_versions = DocumentVersion.objects.filter(document__owner=user).count()
    unfiled_count  = Document.objects.filter(owner=user, folder=None, is_deleted=False).count()

    # Recent version activity (last 8 edits)
    recent_versions = (
        DocumentVersion.objects
        .filter(document__owner=user)
        .select_related('document', 'uploaded_by')
        .order_by('-created_at')[:8]
    )

    # All user folders flat list (for "move to folder" dropdown)
    all_folders = Folder.objects.filter(owner=user).order_by('name')

    return render(request, 'documents/workspace.html', {
        'folder_tree':     folder_tree,
        'docs':            docs,
        'current_folder':  current_folder,
        'panel_title':     panel_title,
        'folder_id':       folder_id,
        'search_q':        search_q,
        'stats': {
            'total_docs':    total_docs,
            'total_folders': total_folders,
            'total_versions': total_versions,
            'unfiled':       unfiled_count,
        },
        'recent_versions': recent_versions,
        'all_folders':     all_folders,
    })


# ── Folder CRUD (AJAX, JSON responses) ───────────────────────

@login_required
@require_POST
def folder_create_api(request):
    data      = json.loads(request.body)
    name      = data.get('name', '').strip()
    parent_id = data.get('parent_id')
    color     = data.get('color', '#6c757d')

    if not name:
        return JsonResponse({'ok': False, 'error': 'Folder name required'})

    parent = None
    if parent_id:
        try:
            parent = Folder.objects.get(id=parent_id, owner=request.user)
        except Folder.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Parent folder not found'}, status=404)

    if Folder.objects.filter(owner=request.user, parent=parent, name=name).exists():
        return JsonResponse({'ok': False, 'error': f'A folder named "{name}" already exists here'})

    folder = Folder.objects.create(name=name, owner=request.user, parent=parent, color=color)
    return JsonResponse({
        'ok': True, 'id': folder.id, 'name': folder.name,
        'color': folder.color, 'parent_id': parent_id,
        'path': folder.get_path(),
    })


@login_required
@require_POST
def folder_rename_api(request, pk):
    try:
        folder = Folder.objects.get(id=pk, owner=request.user)
    except Folder.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Not found'}, status=404)

    data = json.loads(request.body)
    name = data.get('name', '').strip()
    if not name:
        return JsonResponse({'ok': False, 'error': 'Name required'})

    folder.name = name
    folder.save(update_fields=['name', 'updated_at'])
    return JsonResponse({'ok': True, 'name': folder.name})


@login_required
@require_POST
def folder_delete_api(request, pk):
    try:
        folder = Folder.objects.get(id=pk, owner=request.user)
    except Folder.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Not found'}, status=404)

    # Move documents up to the parent folder (don't orphan them)
    Document.objects.filter(folder=folder, owner=request.user).update(folder=folder.parent)
    folder.delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def document_move_api(request, pk):
    try:
        doc = Document.objects.get(id=pk, owner=request.user, is_deleted=False)
    except Document.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Not found'}, status=404)

    data      = json.loads(request.body)
    folder_id = data.get('folder_id')

    if folder_id:
        try:
            folder = Folder.objects.get(id=folder_id, owner=request.user)
            doc.folder = folder
        except Folder.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Folder not found'}, status=404)
    else:
        doc.folder = None   # move to Unfiled

    doc.save(update_fields=['folder'])
    return JsonResponse({'ok': True, 'folder_name': doc.folder.name if doc.folder else None})


# ============================================================
# AGENT SETTINGS — full UI setup + process control
# ============================================================

_AGENT_DIR         = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'desktop_agent')
_AGENT_CONFIG_PATH = os.path.join(_AGENT_DIR, 'config.json')
_AGENT_PID_PATH    = os.path.join(_AGENT_DIR, 'agent.pid')
_AGENT_SCRIPT      = os.path.join(_AGENT_DIR, 'agent.py')

_DEFAULT_CONFIG = {
    'server_url': 'http://localhost:8000',
    'username': '',
    'password': '',
    'watch_folders': [],
    'sync': {'debounce_seconds': 3, 'heartbeat_interval_seconds': 60,
             'retry_on_failure': True, 'max_retries': 5},
    'startup': {'run_on_login': False, 'minimize_to_tray': True, 'show_notifications': True},
    'log': {'level': 'INFO', 'file': 'desktop_agent.log', 'max_size_mb': 10},
}


def _read_agent_config():
    try:
        with open(_AGENT_CONFIG_PATH, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        cfg.pop('_comment', None)
        return cfg
    except Exception:
        return dict(_DEFAULT_CONFIG)


def _write_agent_config(cfg):
    with open(_AGENT_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)


def _pid_is_running(pid):
    """
    Return True if a process with this PID is alive.
    Uses a Windows-native OpenProcess check so we avoid the bugs in
    os.kill(pid, 0) on Windows + Python 3.12 (WinError 87, SystemError, etc.).
    Falls back to os.kill on non-Windows.
    """
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == 'nt':
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        # Check exit code — if process finished, GetExitCodeProcess returns
        # something other than STILL_ACTIVE (259).
        exit_code = ctypes.c_ulong(0)
        alive = False
        if ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            alive = (exit_code.value == 259)   # 259 = STILL_ACTIVE
        ctypes.windll.kernel32.CloseHandle(handle)
        return alive
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def _agent_process_status():
    """Return (is_running, pid_or_None).
    Checks both the web-UI pid file and the APPDATA pid file (written by the popup wizard).
    """
    _appdata = os.environ.get('APPDATA', '')
    candidate_paths = [
        _AGENT_PID_PATH,
        os.path.join(_appdata, 'DocuVaultAgent', 'agent.pid') if _appdata else None,
    ]

    for pid_path in candidate_paths:
        if not pid_path or not os.path.exists(pid_path):
            continue
        try:
            with open(pid_path) as f:
                pid = int(f.read().strip())
        except (ValueError, OSError):
            try:
                os.remove(pid_path)
            except OSError:
                pass
            continue

        if _pid_is_running(pid):
            return True, pid

        # Stale PID — clean up
        try:
            os.remove(pid_path)
        except OSError:
            pass

    return False, None


@login_required
def workspace_agent_view(request):
    from .agent_api import AgentToken
    user = request.user
    cfg  = _read_agent_config()
    all_folders = Folder.objects.filter(owner=user).order_by('name')

    recent_syncs = (
        ActivityLog.objects
        .filter(user=user, action__in=['create', 'edit'],
                description__icontains='Desktop Agent')
        .select_related('document')
        .order_by('-created_at')[:15]
    )

    agent_online = False
    agent_last   = None
    try:
        tok = AgentToken.objects.get(user=user, is_active=True)
        agent_last = tok.last_used
        if agent_last:
            agent_online = (timezone.now() - agent_last).total_seconds() <= 120
    except AgentToken.DoesNotExist:
        pass

    proc_running, proc_pid = _agent_process_status()

    exe_built = os.path.exists(os.path.join(_AGENT_DIR, 'dist', 'DocuVaultAgent.exe'))

    steps = [
        ('1', '⬇️', 'Download', 'Click Download Agent on this page'),
        ('2', '🖱️', 'Double-click', 'Open DocuVaultAgent.exe — setup wizard appears automatically'),
        ('3', '✅', 'Done', 'Agent runs silently in background. No terminal ever needed.'),
    ]

    return render(request, 'documents/workspace_agent.html', {
        'cfg':          cfg,
        'all_folders':  all_folders,
        'recent_syncs': recent_syncs,
        'agent_online': agent_online,
        'agent_last':   agent_last,
        'proc_running': proc_running,
        'proc_pid':     proc_pid,
        'agent_dir':    _AGENT_DIR,
        'server_url':   cfg.get('server_url', 'http://localhost:8000'),
        'exe_built':    exe_built,
        'steps':        steps,
    })


# ── AJAX: save full config ────────────────────────────────────
@login_required
@require_POST
def agent_config_save_view(request):
    """Save entire config.json from the UI form (AJAX POST, JSON body)."""
    try:
        data = json.loads(request.body)
    except ValueError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'})

    cfg = _read_agent_config()

    # Basic fields
    if 'server_url' in data:
        cfg['server_url'] = data['server_url'].strip().rstrip('/')
    if 'username' in data:
        cfg['username'] = data['username'].strip()
    if 'password' in data and data['password']:   # only update if non-empty
        cfg['password'] = data['password']
    if 'debounce' in data:
        cfg.setdefault('sync', {})['debounce_seconds'] = int(data['debounce'])
    if 'heartbeat' in data:
        cfg.setdefault('sync', {})['heartbeat_interval_seconds'] = int(data['heartbeat'])

    # Watch folders (full replacement)
    if 'watch_folders' in data:
        cleaned = []
        for wf in data['watch_folders']:
            path_val = wf.get('path', '').strip()
            if not path_val:
                continue
            entry = {
                'path':      path_val,
                'recursive': bool(wf.get('recursive', True)),
                'category':  wf.get('category', 'General').strip(),
                'extensions': [e.strip() for e in wf.get('extensions', []) if e.strip()],
            }
            fid = wf.get('folder_id')
            if fid:
                try:
                    f_obj = Folder.objects.get(id=int(fid), owner=request.user)
                    entry['folder_id']   = f_obj.id
                    entry['folder_name'] = f_obj.name
                except (Folder.DoesNotExist, ValueError):
                    pass
            cleaned.append(entry)
        cfg['watch_folders'] = cleaned

    _write_agent_config(cfg)
    return JsonResponse({'ok': True, 'message': 'Configuration saved'})


# ── AJAX: start agent process ─────────────────────────────────
@login_required
@require_POST
def agent_process_start_view(request):
    """Launch agent.py as a background subprocess."""
    import subprocess, sys
    running, pid = _agent_process_status()
    if running:
        return JsonResponse({'ok': True, 'message': f'Already running (PID {pid})', 'pid': pid})

    if not os.path.exists(_AGENT_SCRIPT):
        return JsonResponse({'ok': False, 'error': f'agent.py not found at {_AGENT_SCRIPT}'})

    cfg = _read_agent_config()
    if not cfg.get('username') or not cfg.get('password'):
        return JsonResponse({'ok': False, 'error': 'Save credentials first before starting the agent.'})

    try:
        # Use the same Python executable as the Django process
        proc = subprocess.Popen(
            [sys.executable, _AGENT_SCRIPT, '--no-tray'],
            cwd=_AGENT_DIR,
            stdout=open(os.path.join(_AGENT_DIR, 'desktop_agent.log'), 'a'),
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
        )
        # Write PID file
        with open(_AGENT_PID_PATH, 'w') as f:
            f.write(str(proc.pid))
        return JsonResponse({'ok': True, 'pid': proc.pid, 'message': f'Agent started (PID {proc.pid})'})
    except Exception as exc:
        return JsonResponse({'ok': False, 'error': str(exc)})


# ── AJAX: stop agent process ──────────────────────────────────
@login_required
@require_POST
def agent_process_stop_view(request):
    """Terminate the running agent process (by PID or by process name)."""
    import signal as _sig
    import subprocess

    running, pid = _agent_process_status()

    if os.name == 'nt':
        killed = False

        # 1. Kill by PID (includes process tree with /T)
        if pid:
            subprocess.call(
                ['taskkill', '/F', '/T', '/PID', str(pid)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            killed = True

        # 2. Fallback: kill any DocuVaultAgent.exe still running
        subprocess.call(
            ['taskkill', '/F', '/IM', 'DocuVaultAgent.exe'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        # 3. Clean up both PID files
        _appdata = os.environ.get('APPDATA', '')
        for pid_path in [
            _AGENT_PID_PATH,
            os.path.join(_appdata, 'DocuVaultAgent', 'agent.pid') if _appdata else None,
        ]:
            if pid_path:
                try:
                    os.remove(pid_path)
                except OSError:
                    pass

        msg = f'Agent stopped (PID {pid})' if pid else 'Agent stopped'
        return JsonResponse({'ok': True, 'message': msg})

    else:
        # Linux / macOS
        if not running:
            return JsonResponse({'ok': True, 'message': 'Agent is not running'})
        try:
            os.kill(pid, _sig.SIGTERM)
            try:
                os.remove(_AGENT_PID_PATH)
            except OSError:
                pass
            return JsonResponse({'ok': True, 'message': f'Agent stopped (PID {pid})'})
        except Exception as exc:
            return JsonResponse({'ok': False, 'error': str(exc)})


# ── AJAX: get current process status ─────────────────────────
@login_required
def agent_process_status_view(request):
    from .agent_api import AgentToken
    running, pid = _agent_process_status()

    agent_online = False
    agent_last   = None
    try:
        tok = AgentToken.objects.get(user=request.user, is_active=True)
        agent_last = tok.last_used
        if agent_last:
            agent_online = (timezone.now() - agent_last).total_seconds() <= 120
    except AgentToken.DoesNotExist:
        pass

    return JsonResponse({
        'ok':           True,
        'proc_running': running,
        'pid':          pid,
        'online':       agent_online,
        'last_seen':    agent_last.isoformat() if agent_last else None,
    })


# ── Download agent package ────────────────────────────────────
@login_required
def agent_download_view(request):
    """
    GET /workspace/agent/download/
    Serves DocuVaultAgent.exe if built, otherwise a ready-to-run ZIP
    containing agent.py + setup_wizard.py + requirements.txt + install.bat
    so the user can run it with Python directly.
    """
    import zipfile, io

    # Prefer pre-built exe (PyInstaller puts it in dist/)
    exe_path = os.path.join(_AGENT_DIR, 'dist', 'DocuVaultAgent.exe')
    if os.path.exists(exe_path):
        with open(exe_path, 'rb') as f:
            data = f.read()
        resp = HttpResponse(data, content_type='application/octet-stream')
        resp['Content-Disposition'] = 'attachment; filename="DocuVaultAgent.exe"'
        return resp

    # Fallback ZIP — works if the client PC has Python installed.
    # Primary launcher = DocuVaultAgent.vbs  (double-click, no terminal)
    # Backup launcher  = install.bat         (installs deps first time)

    server_url = request.build_absolute_uri('/').rstrip('/')

    # Portable VBS: finds Python automatically, no hardcoded paths
    vbs_content = (
        '\'  DocuVault Agent Launcher\r\n'
        '\'  Double-click this file to start.\r\n'
        '\'  Requires Python 3.10+ — get it from https://www.python.org\r\n\r\n'
        'Dim objFSO, strDir, WshShell\r\n'
        'Set objFSO   = CreateObject("Scripting.FileSystemObject")\r\n'
        'Set WshShell = CreateObject("WScript.Shell")\r\n'
        'strDir = objFSO.GetParentFolderName(WScript.ScriptFullName)\r\n\r\n'
        'On Error Resume Next\r\n'
        'WshShell.Run "pythonw """ & strDir & "\\agent.py""", 0, False\r\n'
        'If Err.Number <> 0 Then\r\n'
        '    Err.Clear\r\n'
        '    WshShell.Run "python """ & strDir & "\\agent.py""", 1, False\r\n'
        'End If\r\n'
    )

    install_bat = (
        '@echo off\r\n'
        'cd /d "%~dp0"\r\n'
        'echo DocuVault Agent — First-time install\r\n'
        'echo =====================================\r\n'
        'python --version >nul 2>&1\r\n'
        'if errorlevel 1 (\r\n'
        '    echo ERROR: Python not found.\r\n'
        '    echo Download Python from https://www.python.org/downloads/\r\n'
        '    echo Make sure to tick "Add Python to PATH" during install.\r\n'
        '    pause & exit /b 1\r\n'
        ')\r\n'
        'echo Installing required packages...\r\n'
        'pip install -r requirements.txt --quiet\r\n'
        'echo.\r\n'
        'echo Done! Double-click DocuVaultAgent.vbs to start the agent.\r\n'
        'pause\r\n'
    )

    readme = (
        'DocuVault Desktop Agent\r\n'
        '=======================\r\n\r\n'
        'OPTION A — If you have Python installed (quick start):\r\n'
        '  1. Run install.bat  (one-time, installs packages)\r\n'
        '  2. Double-click DocuVaultAgent.vbs\r\n'
        '  3. Setup wizard opens — enter server + credentials + folder\r\n'
        '  4. Click Launch Agent — runs in background automatically\r\n\r\n'
        'OPTION B — Ask your admin to build DocuVaultAgent.exe\r\n'
        '  Then you just double-click the .exe — no Python needed.\r\n\r\n'
        f'Your DocuVault server: {server_url}\r\n'
    )

    FILES_TO_INCLUDE = [
        'agent.py',
        'setup_wizard.py',
        'requirements.txt',
    ]

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname in FILES_TO_INCLUDE:
            fpath = os.path.join(_AGENT_DIR, fname)
            if os.path.exists(fpath):
                zf.write(fpath, f'DocuVaultAgent/{fname}')
        # Portable VBS is the main launcher — named prominently
        zf.writestr('DocuVaultAgent/DocuVaultAgent.vbs', vbs_content)
        zf.writestr('DocuVaultAgent/install.bat', install_bat)
        zf.writestr('DocuVaultAgent/README.txt', readme)

    buf.seek(0)
    resp = HttpResponse(buf.read(), content_type='application/zip')
    resp['Content-Disposition'] = 'attachment; filename="DocuVaultAgent.zip"'
    return resp


# ── Download RunAgent.bat (Python-based launcher) ─────────────
@login_required
def agent_bat_download_view(request):
    """
    GET /workspace/agent/download/bat/
    Serves a ZIP containing RunAgent.bat, StartAgentBackground.bat,
    agent.py, setup_wizard.py, and requirements.txt — everything needed
    to run the agent on a PC that already has Python installed.
    The batch files are pre-configured with this server's URL.
    """
    import zipfile, io

    server_url = request.build_absolute_uri('/').rstrip('/')

    # Read the bat files from disk (they're already in desktop_agent/)
    run_bat_path = os.path.join(_AGENT_DIR, 'RunAgent.bat')
    bg_bat_path  = os.path.join(_AGENT_DIR, 'StartAgentBackground.bat')

    run_bat_content = open(run_bat_path, 'r', encoding='utf-8').read() if os.path.exists(run_bat_path) else ''
    bg_bat_content  = open(bg_bat_path,  'r', encoding='utf-8').read() if os.path.exists(bg_bat_path)  else ''

    readme = (
        'DocuVault Desktop Agent — Python Launcher\r\n'
        '==========================================\r\n\r\n'
        'Requirements: Python 3.10+ with packages installed.\r\n\r\n'
        'QUICK START\r\n'
        '-----------\r\n'
        '1. Extract this ZIP somewhere (e.g. C:\\DocuVaultAgent\\)\r\n'
        '2. Double-click RunAgent.bat\r\n'
        '   - First run: setup wizard opens — enter server URL, login, watch folder\r\n'
        '   - Next runs: status popup with Start / Stop controls\r\n\r\n'
        'SILENT / BACKGROUND MODE\r\n'
        '------------------------\r\n'
        'Run:  StartAgentBackground.bat\r\n'
        'Or:   RunAgent.bat --no-tray\r\n'
        'This starts the agent with no window — logs go to desktop_agent.log\r\n\r\n'
        'ADD TO WINDOWS STARTUP (auto-start on login)\r\n'
        '--------------------------------------------\r\n'
        '1. Press Win+R and type:  shell:startup\r\n'
        '2. Copy a shortcut of StartAgentBackground.bat into that folder\r\n\r\n'
        f'Your DocuVault server: {server_url}\r\n'
    )

    FILES_TO_INCLUDE = ['agent.py', 'setup_wizard.py', 'requirements.txt']

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname in FILES_TO_INCLUDE:
            fpath = os.path.join(_AGENT_DIR, fname)
            if os.path.exists(fpath):
                zf.write(fpath, f'DocuVaultAgent/{fname}')
        if run_bat_content:
            zf.writestr('DocuVaultAgent/RunAgent.bat', run_bat_content)
        if bg_bat_content:
            zf.writestr('DocuVaultAgent/StartAgentBackground.bat', bg_bat_content)
        zf.writestr('DocuVaultAgent/README.txt', readme)

    buf.seek(0)
    resp = HttpResponse(buf.read(), content_type='application/zip')
    resp['Content-Disposition'] = 'attachment; filename="DocuVaultAgent-bat.zip"'
    return resp


# ── Build .exe in browser ─────────────────────────────────────
_BUILD_LOG_PATH = os.path.join(_AGENT_DIR, 'build.log')

@login_required
@require_POST
def agent_build_exe_view(request):
    """Start a background PyInstaller build and return immediately."""
    if not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': 'Admin only'})

    import subprocess, sys

    exe_path = os.path.join(_AGENT_DIR, 'dist', 'DocuVaultAgent.exe')

    # Kill any running DocuVaultAgent.exe so the file isn't locked during build
    if os.name == 'nt':
        subprocess.call(
            ['taskkill', '/F', '/IM', 'DocuVaultAgent.exe'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    # Remove the old exe so PyInstaller isn't blocked by a locked file
    if os.path.exists(exe_path):
        try:
            os.remove(exe_path)
        except OSError:
            pass  # still locked — build will fail with a clear error

    # Clear old log
    with open(_BUILD_LOG_PATH, 'w', encoding='utf-8') as f:
        f.write('Build started...\n')

    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile', '--noconsole',
        '--name', 'DocuVaultAgent',
        '--hidden-import', 'setup_wizard',
        '--hidden-import', 'tkinter',
        '--hidden-import', 'tkinter.filedialog',
        '--hidden-import', 'pystray',
        '--hidden-import', 'PIL',
        '--hidden-import', 'watchdog',
        '--hidden-import', 'requests',
        '--hidden-import', 'dateutil',
        '--hidden-import', 'winreg',
        'agent.py',
    ]

    log_file = open(_BUILD_LOG_PATH, 'a', encoding='utf-8')
    subprocess.Popen(
        cmd, cwd=_AGENT_DIR,
        stdout=log_file, stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
    )
    return JsonResponse({'ok': True, 'message': 'Build started'})


@login_required
def agent_build_log_view(request):
    """Poll build progress — returns last N lines of build.log."""
    try:
        with open(_BUILD_LOG_PATH, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        last = lines[-60:] if len(lines) > 60 else lines
        exe_path = os.path.join(_AGENT_DIR, 'dist', 'DocuVaultAgent.exe')
        built = os.path.exists(exe_path)
        return JsonResponse({'ok': True, 'log': ''.join(last), 'built': built})
    except FileNotFoundError:
        return JsonResponse({'ok': True, 'log': '', 'built': False})