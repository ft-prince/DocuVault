from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (
    User, Role, Document, Category, Tag, DocumentVersion,
    DocumentComment, SharedLink, Favorite, ActivityLog, Notification
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom user admin"""
    list_display = ('username', 'email', 'user_type', 'role', 'is_active', 'created_at')
    list_filter = ('user_type', 'is_active', 'role', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'role', 'bio', 'avatar', 'phone', 'department', 'last_activity')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'role', 'email', 'first_name', 'last_name')
        }),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Role admin"""
    list_display = ('name', 'level', 'is_default', 'user_count', 'created_at')
    list_filter = ('is_default', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('-level',)
    
    def user_count(self, obj):
        return obj.users.count()
    user_count.short_description = 'Users'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Category admin"""
    list_display = ('name', 'parent', 'color_badge', 'document_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    def color_badge(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 5px 10px; border-radius: 3px; color: white;">{}</span>',
            obj.color,
            obj.name
        )
    color_badge.short_description = 'Color'
    
    def document_count(self, obj):
        return obj.documents.filter(is_deleted=False).count()
    document_count.short_description = 'Documents'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Tag admin"""
    list_display = ('name', 'document_count', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)
    
    def document_count(self, obj):
        return obj.documents.count()
    document_count.short_description = 'Documents'


class DocumentVersionInline(admin.TabularInline):
    """Inline for document versions"""
    model = DocumentVersion
    extra = 0
    readonly_fields = ('version_number', 'file_size', 'uploaded_by', 'created_at')
    fields = ('version_number', 'file', 'file_size', 'uploaded_by', 'change_note', 'created_at')


class DocumentCommentInline(admin.TabularInline):
    """Inline for document comments"""
    model = DocumentComment
    extra = 0
    readonly_fields = ('user', 'created_at')
    fields = ('user', 'content', 'created_at')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Document admin"""
    list_display = (
        'title', 'owner', 'category', 'access_level', 'version',
        'views_count', 'downloads_count', 'is_locked', 'is_deleted', 'created_at'
    )
    list_filter = ('access_level', 'is_locked', 'is_deleted', 'category', 'created_at')
    search_fields = ('title', 'description', 'owner__username')
    ordering = ('-created_at',)
    readonly_fields = ('views_count', 'downloads_count', 'version', 'created_at', 'updated_at')
    filter_horizontal = ('tags', 'shared_with')
    inlines = [DocumentVersionInline, DocumentCommentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'file', 'owner', 'category', 'tags')
        }),
        ('Access Control', {
            'fields': ('access_level', 'required_role_level', 'shared_with')
        }),
        ('Settings', {
            'fields': ('allow_comments', 'allow_download', 'is_locked', 'locked_by')
        }),
        ('Metadata', {
            'fields': ('file_size', 'file_type', 'version', 'views_count', 'downloads_count')
        }),
        ('Status', {
            'fields': ('is_deleted', 'deleted_at', 'created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new document
            obj.owner = request.user
        super().save_model(request, obj, form, change)


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    """Document version admin"""
    list_display = ('document', 'version_number', 'uploaded_by', 'file_size', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('document__title', 'uploaded_by__username', 'change_note')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(DocumentComment)
class DocumentCommentAdmin(admin.ModelAdmin):
    """Document comment admin"""
    list_display = ('document', 'user', 'content_preview', 'parent', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('document__title', 'user__username', 'content')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(SharedLink)
class SharedLinkAdmin(admin.ModelAdmin):
    """Shared link admin"""
    list_display = (
        'document', 'created_by', 'token', 'expires_at',
        'access_count', 'max_access_count', 'is_active', 'is_valid_status'
    )
    list_filter = ('is_active', 'created_at', 'expires_at')
    search_fields = ('document__title', 'created_by__username', 'token')
    ordering = ('-created_at',)
    readonly_fields = ('token', 'access_count', 'created_at')
    
    def is_valid_status(self, obj):
        return obj.is_valid()
    is_valid_status.boolean = True
    is_valid_status.short_description = 'Valid'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Favorite admin"""
    list_display = ('user', 'document', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'document__title')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Activity log admin"""
    list_display = ('user', 'document', 'action', 'ip_address', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'document__title', 'description', 'ip_address')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation
    
    def has_change_permission(self, request, obj=None):
        return False  # Don't allow editing


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Notification admin"""
    list_display = ('recipient', 'sender', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'sender__username', 'title', 'message')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = 'Mark selected notifications as read'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notifications marked as unread.')
    mark_as_unread.short_description = 'Mark selected notifications as unread'