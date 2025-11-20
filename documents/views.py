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
    DocumentComment, SharedLink, Favorite, ActivityLog, Notification
)
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
        return redirect('dashboard')
    
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
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    
    
    return render(request, 'documents/auth/register.html', {'form': form})


def login_view(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect(request.GET.get('next', 'dashboard'))
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
    
    # Get versions
    versions = document.versions.all()[:5]
    
    # Check if favorited
    is_favorited = Favorite.objects.filter(user=request.user, document=document).exists()
    
    # Get recent activity
    recent_activity = document.activity_logs.select_related('user')[:10]
    
    context = {
        'document': document,
        'comments': comments,
        'versions': versions,
        'is_favorited': is_favorited,
        'recent_activity': recent_activity,
        'can_edit': document.can_edit(request.user),
        'can_delete': document.can_delete(request.user),
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
            return redirect('document_detail', pk=document.pk)
    else:
        form = DocumentForm(user=request.user)
    
    return render(request, 'documents/document_form.html', {'form': form, 'action': 'Create'})


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
            old_file = document.file
            document = form.save(commit=False)
            
            # If new file uploaded, create new version
            if 'file' in request.FILES and request.FILES['file']:
                uploaded_file = request.FILES['file']
                document.file_size = uploaded_file.size
                document.file_type = uploaded_file.content_type
                document.version += 1
                
                # Create new version
                DocumentVersion.objects.create(
                    document=document,
                    version_number=document.version,
                    file=document.file,
                    file_size=document.file_size,
                    uploaded_by=request.user,
                    change_note=request.POST.get('change_note', 'Updated document')
                )
            
            document.save()
            form.save_m2m()
            
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
    
    if request.method == 'POST':
        form = SharedLinkForm(request.POST)
        if form.is_valid():
            link = form.save(commit=False)
            link.document = document
            link.created_by = request.user
            link.save()
            
            messages.success(request, 'Shareable link created successfully!')
            return redirect('document_detail', pk=document_pk)
    else:
        form = SharedLinkForm()
    
    return render(request, 'documents/shared_link_form.html', {
        'form': form,
        'document': document
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