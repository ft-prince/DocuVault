from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.utils.html import format_html
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import path, reverse
from django.contrib import messages as django_messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from .models import (
    Organization, User, Role, Document, Category, Tag, DocumentVersion,
    DocumentComment, SharedLink, Favorite, ActivityLog, Notification,
    ChatSession, ChatMessage, DocumentEmbedding, ChatSessionShare,
)


# ============================================================
# ORGANIZATION ADMIN — with inline org-admin creation
# ============================================================

class OrgAdminUserForm(UserCreationForm):
    """Form used inside the inline to create a new org admin with hashed password."""
    first_name = forms.CharField(max_length=150, required=True)
    last_name  = forms.CharField(max_length=150, required=True)
    email      = forms.EmailField(required=True)

    class Meta:
        model  = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')


class OrgAdminChangeForm(forms.ModelForm):
    """Read-only display form for existing org admins — no password fields."""
    class Meta:
        model  = User
        fields = ('username', 'first_name', 'last_name', 'email', 'employee_code', 'is_approved', 'role')


class OrgAdminInline(admin.StackedInline):
    """
    Inline on the Organization page.
    Shows existing org admins (info only) and lets you create a brand-new admin account.
    """
    model       = User
    fk_name     = 'organization'
    extra       = 0
    verbose_name        = 'Organization Admin'
    verbose_name_plural = 'Organization Admins'
    can_delete  = False

    def get_queryset(self, request):
        return super().get_queryset(request).filter(user_type='admin')

    def get_form(self, request, obj=None, **kwargs):
        # Existing admin row → show info only, no passwords
        if obj is not None:
            kwargs['form'] = OrgAdminChangeForm
            kwargs['fields'] = ('username', 'first_name', 'last_name', 'email',
                                'employee_code', 'is_approved', 'role')
            return super().get_form(request, obj, **kwargs)
        # New admin row → full creation form with passwords
        kwargs['form'] = OrgAdminUserForm
        kwargs['fields'] = ('username', 'first_name', 'last_name', 'email',
                            'password1', 'password2', 'employee_code', 'is_approved', 'role')
        return super().get_form(request, obj, **kwargs)

    def save_new(self, form, commit=True):
        user = form.save(commit=False)
        if 'password1' in form.cleaned_data:
            user.set_password(form.cleaned_data['password1'])
        user.user_type   = 'admin'
        user.is_approved = True
        if commit:
            user.save()
        return user

    def get_extra(self, request, obj=None, **kwargs):
        # Show 1 blank creation form only when the org has no admin yet
        if obj and obj.members.filter(user_type='admin').exists():
            return 0
        return 1


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Manage tenant organizations and their admins."""
    list_display    = ('name', 'org_admin_info', 'member_count', 'pending_count', 'is_active', 'created_at')
    list_filter     = ('is_active', 'created_at')
    search_fields   = ('name',)
    ordering        = ('name',)
    readonly_fields = ('created_at', 'org_admin_info', 'assign_existing_user_panel')
    inlines         = [OrgAdminInline]

    fieldsets = (
        (None,   {'fields': ('name', 'is_active')}),
        ('Info', {'fields': ('created_at', 'org_admin_info')}),
        ('Assign Existing User', {
            'fields': ('assign_existing_user_panel',),
            'description': 'Add an already-registered user to this organisation.',
        }),
    )

    # ── Custom URL for the assign POST ──────────────────────────
    def get_urls(self):
        return [
            path('<int:org_id>/assign-user/',
                 self.admin_site.admin_view(self.assign_user_view),
                 name='org_assign_user'),
        ] + super().get_urls()

    def assign_user_view(self, request, org_id):
        org = get_object_or_404(Organization, pk=org_id)
        available = User.objects.exclude(organization=org).order_by('username')
        error = None

        if request.method == 'POST':
            user_id = request.POST.get('user_id')
            if user_id:
                try:
                    user = User.objects.get(pk=user_id)
                    user.organization = org
                    user.is_approved = True
                    user.save()
                    django_messages.success(
                        request,
                        f'{user.username} assigned to {org.name}.'
                    )
                    return redirect(reverse('admin:documents_organization_change', args=[org_id]))
                except User.DoesNotExist:
                    error = 'User not found.'
            else:
                error = 'Please select a user.'

        return render(request, 'admin/assign_user_to_org.html', {
            'org': org,
            'available': available,
            'error': error,
            **self.admin_site.each_context(request),
        })

    # ── Readonly panel rendered inside the change form ───────────
    def assign_existing_user_panel(self, obj):
        if not obj or not obj.pk:
            return format_html('<em style="color:#9ca3af;">Save the organisation first.</em>')
        url = reverse('admin:org_assign_user', args=[obj.pk])
        return format_html(
            '<a href="{}" style="padding:.4rem 1rem;background:#7c3aed;color:#fff;'
            'border-radius:6px;font-size:.875rem;font-weight:600;text-decoration:none;">'
            'Assign Existing User</a>'
            '&nbsp;<span style="font-size:.8rem;color:#6b7280;">Opens a separate page</span>',
            url,
        )
    assign_existing_user_panel.short_description = 'Assign user'

    def org_admin_info(self, obj):
        admins = obj.members.filter(user_type='admin')
        if not admins.exists():
            return format_html('<span style="color:#9ca3af;">No admin assigned</span>')
        rows = ''.join(
            f'<div style="margin-bottom:.3rem;">'
            f'<strong>{a.get_full_name() or a.username}</strong> '
            f'&lt;{a.email}&gt;'
            f'</div>'
            for a in admins
        )
        return format_html(rows)
    org_admin_info.short_description = 'Admin(s)'

    def member_count(self, obj):
        return obj.members.filter(is_approved=True).count()
    member_count.short_description = 'Members'

    def pending_count(self, obj):
        count = obj.members.filter(is_approved=False, is_active=True).count()
        if count:
            return format_html(
                '<span style="background:#fef9c3;color:#92400e;padding:2px 8px;'
                'border-radius:12px;font-weight:600;">{}</span>', count
            )
        return '—'
    pending_count.short_description = 'Pending'


# ============================================================
# USER ADMIN
# ============================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom user admin"""
    list_display  = ('username', 'email', 'organization', 'user_type', 'role',
                     'is_approved', 'is_active', 'created_at')
    list_filter   = ('user_type', 'is_approved', 'is_active', 'role', 'organization', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'employee_code')
    ordering      = ('-created_at',)
    actions       = ['approve_users', 'revoke_approval', 'assign_to_organization']

    # last_activity has auto_now=True → non-editable → must NOT appear in fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Organisation & Role', {
            'fields': ('organization', 'user_type', 'role', 'is_approved', 'employee_code')
        }),
        ('Profile', {
            'fields': ('bio', 'avatar', 'phone', 'department')
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Organisation & Role', {
            'fields': ('organization', 'user_type', 'role', 'email',
                       'first_name', 'last_name', 'employee_code', 'is_approved')
        }),
    )

    def approve_users(self, request, queryset):
        updated = queryset.filter(is_approved=False).update(is_approved=True)
        self.message_user(request, f'{updated} user(s) approved.')
    approve_users.short_description = 'Approve selected users'

    def revoke_approval(self, request, queryset):
        updated = queryset.exclude(user_type='admin').filter(is_approved=True).update(is_approved=False)
        self.message_user(request, f'{updated} user(s) approval revoked.')
    revoke_approval.short_description = 'Revoke approval (non-admins only)'

    def assign_to_organization(self, request, queryset):
        if 'apply' in request.POST:
            org_id = request.POST.get('organization')
            if org_id:
                org = Organization.objects.get(pk=org_id)
                updated = queryset.update(organization=org)
                self.message_user(request, f'{updated} user(s) assigned to {org.name}.')
                return
        return render(request, 'admin/assign_organization.html', {
            'users': queryset,
            'organizations': Organization.objects.filter(is_active=True).order_by('name'),
            'action': 'assign_to_organization',
            ACTION_CHECKBOX_NAME: request.POST.getlist(ACTION_CHECKBOX_NAME),
        })
    assign_to_organization.short_description = 'Assign selected users to an organization'


# ============================================================
# ROLE ADMIN
# ============================================================

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display  = ('name', 'level', 'is_default', 'user_count', 'created_at')
    list_filter   = ('is_default', 'created_at')
    search_fields = ('name', 'description')
    ordering      = ('-level',)

    def user_count(self, obj):
        return obj.users.count()
    user_count.short_description = 'Users'


# ============================================================
# CATEGORY / TAG ADMIN
# ============================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ('name', 'parent', 'color_badge', 'document_count', 'created_at')
    list_filter   = ('created_at',)
    search_fields = ('name', 'description')
    ordering      = ('name',)

    def color_badge(self, obj):
        return format_html(
            '<span style="background:{};padding:4px 10px;border-radius:3px;color:#fff;">{}</span>',
            obj.color, obj.name,
        )
    color_badge.short_description = 'Color'

    def document_count(self, obj):
        return obj.documents.filter(is_deleted=False).count()
    document_count.short_description = 'Documents'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display  = ('name', 'document_count', 'created_at')
    search_fields = ('name',)
    ordering      = ('name',)

    def document_count(self, obj):
        return obj.documents.count()
    document_count.short_description = 'Documents'


# ============================================================
# DOCUMENT ADMIN
# ============================================================

class DocumentVersionInline(admin.TabularInline):
    model  = DocumentVersion
    extra  = 0
    readonly_fields = ('version_number', 'file_size', 'uploaded_by', 'created_at')
    fields = ('version_number', 'file', 'file_size', 'uploaded_by', 'change_note', 'created_at')


class DocumentCommentInline(admin.TabularInline):
    model  = DocumentComment
    extra  = 0
    readonly_fields = ('user', 'created_at')
    fields = ('user', 'content', 'created_at')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display  = (
        'title', 'owner', 'category', 'access_level', 'version',
        'views_count', 'downloads_count', 'is_locked', 'is_deleted', 'created_at',
    )
    list_filter   = ('access_level', 'is_locked', 'is_deleted', 'category', 'created_at')
    search_fields = ('title', 'description', 'owner__username')
    ordering      = ('-created_at',)
    readonly_fields = ('views_count', 'downloads_count', 'version', 'created_at', 'updated_at')
    filter_horizontal = ('tags', 'shared_with')
    inlines       = [DocumentVersionInline, DocumentCommentInline]

    fieldsets = (
        ('Basic Information', {'fields': ('title', 'description', 'file', 'owner', 'category', 'tags')}),
        ('Access Control',    {'fields': ('access_level', 'required_role_level', 'shared_with')}),
        ('Settings',          {'fields': ('allow_comments', 'allow_download', 'is_locked', 'locked_by')}),
        ('Metadata',          {'fields': ('file_size', 'file_type', 'version', 'views_count', 'downloads_count')}),
        ('Status',            {'fields': ('is_deleted', 'deleted_at', 'created_at', 'updated_at')}),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.owner = request.user
        super().save_model(request, obj, form, change)


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display  = ('document', 'version_number', 'uploaded_by', 'file_size', 'created_at')
    list_filter   = ('created_at',)
    search_fields = ('document__title', 'uploaded_by__username', 'change_note')
    ordering      = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(DocumentComment)
class DocumentCommentAdmin(admin.ModelAdmin):
    list_display  = ('document', 'user', 'content_preview', 'parent', 'created_at')
    list_filter   = ('created_at',)
    search_fields = ('document__title', 'user__username', 'content')
    ordering      = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(SharedLink)
class SharedLinkAdmin(admin.ModelAdmin):
    list_display  = (
        'document', 'created_by', 'token', 'expires_at',
        'access_count', 'max_access_count', 'is_active', 'is_valid_status',
    )
    list_filter   = ('is_active', 'created_at', 'expires_at')
    search_fields = ('document__title', 'created_by__username', 'token')
    ordering      = ('-created_at',)
    readonly_fields = ('token', 'access_count', 'created_at')

    def is_valid_status(self, obj):
        return obj.is_valid()
    is_valid_status.boolean = True
    is_valid_status.short_description = 'Valid'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display  = ('user', 'document', 'created_at')
    list_filter   = ('created_at',)
    search_fields = ('user__username', 'document__title')
    ordering      = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display  = ('user', 'document', 'action', 'ip_address', 'created_at')
    list_filter   = ('action', 'created_at')
    search_fields = ('user__username', 'document__title', 'description', 'ip_address')
    ordering      = ('-created_at',)
    readonly_fields = ('created_at',)

    def has_add_permission(self, request):    return False
    def has_change_permission(self, request, obj=None): return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ('recipient', 'sender', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter   = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'sender__username', 'title', 'message')
    ordering      = ('-created_at',)
    readonly_fields = ('created_at',)
    actions       = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        self.message_user(request, f'{queryset.update(is_read=True)} notifications marked as read.')
    mark_as_read.short_description = 'Mark selected as read'

    def mark_as_unread(self, request, queryset):
        self.message_user(request, f'{queryset.update(is_read=False)} notifications marked as unread.')
    mark_as_unread.short_description = 'Mark selected as unread'


# ============================================================
# RAG CHATBOT ADMIN
# ============================================================

class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('message_type', 'content', 'created_at', 'retrieval_time', 'generation_time')
    can_delete = False
    max_num    = 0


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display  = ('user', 'title', 'message_count', 'is_public', 'is_active', 'created_at', 'updated_at')
    list_filter   = ('is_active', 'created_at', 'updated_at')
    search_fields = ('user__username', 'title')
    ordering      = ('-updated_at',)
    readonly_fields = ('created_at', 'updated_at', 'message_count', 'public_share_token')
    filter_horizontal = ('documents',)
    inlines       = [ChatMessageInline]

    def message_count(self, obj):
        return obj.get_message_count()
    message_count.short_description = 'Messages'

    def is_public(self, obj):
        return bool(obj.public_share_token)
    is_public.boolean = True
    is_public.short_description = 'Public'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display  = ('session', 'message_type', 'content_preview', 'created_at', 'retrieval_time', 'generation_time')
    list_filter   = ('message_type', 'created_at')
    search_fields = ('session__user__username', 'content')
    ordering      = ('-created_at',)
    readonly_fields = ('created_at', 'sources', 'retrieval_time', 'generation_time')

    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'


@admin.register(ChatSessionShare)
class ChatSessionShareAdmin(admin.ModelAdmin):
    list_display  = ('session', 'shared_by', 'shared_with', 'created_at')
    list_filter   = ('created_at',)
    search_fields = ('session__title', 'shared_by__username', 'shared_with__username')
    ordering      = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(DocumentEmbedding)
class DocumentEmbeddingAdmin(admin.ModelAdmin):
    list_display  = ('document', 'is_indexed', 'index_status', 'chunk_count', 'embedding_model', 'last_indexed_at', 'retry_count')
    list_filter   = ('is_indexed', 'index_status', 'created_at', 'updated_at')
    search_fields = ('document__title', 'embedding_model', 'error_message')
    ordering      = ('-updated_at',)
    readonly_fields = ('created_at', 'updated_at', 'indexed_at', 'last_indexed_at')
    actions       = ['retry_indexing', 'reset_status']

    def retry_indexing(self, request, queryset):
        self.message_user(request, f'{queryset.update(index_status="pending", error_message="")} documents queued for re-indexing.')
    retry_indexing.short_description = 'Retry indexing'

    def reset_status(self, request, queryset):
        self.message_user(request, f'{queryset.update(index_status="pending", is_indexed=False, retry_count=0, error_message="")} reset.')
    reset_status.short_description = 'Reset to pending'
