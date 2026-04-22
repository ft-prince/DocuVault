from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (
    Organization, User, Role, Document, Category, Tag, DocumentVersion,
    DocumentComment, SharedLink, Favorite, ActivityLog, Notification,
    ChatSession, ChatMessage, DocumentEmbedding, ChatSessionShare,
)


# ============================================================
# ORGANIZATION ADMIN
# ============================================================

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """
    Admin-only: create and manage tenant organizations.
    Users pick from this list during sign-up — no free-text entry allowed.
    """
    list_display  = ('name', 'member_count', 'is_active', 'created_at')
    list_filter   = ('is_active', 'created_at')
    search_fields = ('name',)
    ordering      = ('name',)
    readonly_fields = ('created_at',)

    fieldsets = (
        (None, {'fields': ('name', 'is_active')}),
        ('Info',  {'fields': ('created_at',)}),
    )

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'


# ============================================================
# USER ADMIN
# ============================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom user admin"""
    list_display  = ('username', 'email', 'organization', 'user_type', 'role', 'is_active', 'created_at')
    list_filter   = ('user_type', 'is_active', 'role', 'organization', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering      = ('-created_at',)

    # last_activity has auto_now=True → non-editable → must NOT appear in fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Organisation & Role', {
            'fields': ('organization', 'user_type', 'role')
        }),
        ('Profile', {
            'fields': ('bio', 'avatar', 'phone', 'department')
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Organisation & Role', {
            'fields': ('organization', 'user_type', 'role', 'email', 'first_name', 'last_name')
        }),
    )


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
