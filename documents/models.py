from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models import Q
import uuid
import os


class Role(models.Model):
    """Custom roles for role-based access control"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    level = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Higher level = more privileges (1-100)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_default = models.BooleanField(default=False, help_text="Cannot be deleted if True")

    class Meta:
        ordering = ['-level', 'name']

    def __str__(self):
        return f"{self.name} (Level {self.level})"


class User(AbstractUser):
    """Extended user model with role-based permissions"""
    USER_TYPE_CHOICES = [
        ('guest', 'Guest'),
        ('user', 'Regular User'),
        ('admin', 'Admin'),
    ]
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='user')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.username

    def is_admin(self):
        return self.user_type == 'admin'

    def get_role_level(self):
        if self.is_admin():
            return 100
        return self.role.level if self.role else 1


class Category(models.Model):
    """Document categories for organization"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class name")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_categories')

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Tags for flexible document organization"""
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


def document_upload_path(instance, filename):
    """Generate upload path for documents"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('documents', str(instance.owner.id), filename)


class Document(models.Model):
    """Main document model"""
    ACCESS_LEVEL_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('role', 'Role-Based'),
        ('custom', 'Custom Users'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to=document_upload_path)
    file_size = models.BigIntegerField(default=0, help_text="Size in bytes")
    file_type = models.CharField(max_length=100, blank=True)
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_documents')
    access_level = models.CharField(max_length=10, choices=ACCESS_LEVEL_CHOICES, default='private')
    required_role_level = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Minimum role level required (for role-based access)"
    )
    
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    tags = models.ManyToManyField(Tag, blank=True, related_name='documents')
    
    shared_with = models.ManyToManyField(User, blank=True, related_name='shared_documents')
    
    version = models.IntegerField(default=1)
    is_locked = models.BooleanField(default=False, help_text="Locked documents cannot be edited")
    locked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='locked_documents')
    
    views_count = models.IntegerField(default=0)
    downloads_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Collaboration features
    allow_comments = models.BooleanField(default=True)
    allow_download = models.BooleanField(default=True)
    
    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-updated_at', '-created_at']
        indexes = [
            models.Index(fields=['owner', 'access_level']),
            models.Index(fields=['created_at']),
            models.Index(fields=['title']),
        ]

    def __str__(self):
        return self.title

    def can_view(self, user):
        """Check if user can view this document"""
        if user == self.owner or user.is_admin():
            return True
        
        if self.access_level == 'public':
            return True
        
        if self.access_level == 'private':
            return False
        
        if self.access_level == 'role':
            return user.get_role_level() >= self.required_role_level
        
        if self.access_level == 'custom':
            return user in self.shared_with.all()
        
        return False

    def can_edit(self, user):
        """Check if user can edit this document"""
        if self.is_locked and user != self.locked_by and not user.is_admin():
            return False
        return user == self.owner or user.is_admin()

    def can_delete(self, user):
        """Check if user can delete this document"""
        return user == self.owner or user.is_admin()

    def increment_views(self):
        """Increment view counter"""
        self.views_count += 1
        self.save(update_fields=['views_count'])

    def increment_downloads(self):
        """Increment download counter"""
        self.downloads_count += 1
        self.save(update_fields=['downloads_count'])


class DocumentVersion(models.Model):
    """Track document version history"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    file = models.FileField(upload_to='document_versions/')
    file_size = models.BigIntegerField(default=0)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    change_note = models.TextField(blank=True, help_text="What changed in this version")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version_number']
        unique_together = ['document', 'version_number']

    def __str__(self):
        return f"{self.document.title} - v{self.version_number}"


class DocumentComment(models.Model):
    """Comments on documents"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    content = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.document.title}"


class SharedLink(models.Model):
    """Temporary shareable links for documents"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='shared_links')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_links')
    
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    password = models.CharField(max_length=128, blank=True, help_text="Optional password protection")
    
    expires_at = models.DateTimeField(null=True, blank=True)
    max_access_count = models.IntegerField(null=True, blank=True, help_text="Maximum number of accesses")
    access_count = models.IntegerField(default=0)
    
    allow_download = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Link for {self.document.title}"

    def is_valid(self):
        """Check if link is still valid"""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        if self.max_access_count and self.access_count >= self.max_access_count:
            return False
        return True

    def increment_access(self):
        """Increment access counter"""
        self.access_count += 1
        self.save(update_fields=['access_count'])


class Favorite(models.Model):
    """User favorites/bookmarks"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'document']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.document.title}"


class ActivityLog(models.Model):
    """Track all document activities"""
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('view', 'Viewed'),
        ('download', 'Downloaded'),
        ('edit', 'Edited'),
        ('delete', 'Deleted'),
        ('share', 'Shared'),
        ('comment', 'Commented'),
        ('favorite', 'Favorited'),
        ('restore', 'Restored'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='activity_logs')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document', 'action']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username if self.user else 'Unknown'} {self.action} {self.document.title}"


class Notification(models.Model):
    """User notifications"""
    NOTIFICATION_TYPES = [
        ('document_shared', 'Document Shared'),
        ('document_updated', 'Document Updated'),
        ('comment_added', 'Comment Added'),
        ('comment_reply', 'Comment Reply'),
        ('permission_changed', 'Permission Changed'),
        ('mention', 'Mentioned'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.title}"


# ============================================================
# RAG CHATBOT MODELS
# ============================================================

class ChatSession(models.Model):
    """Chat session for RAG chatbot"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=255, default='New Conversation')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Optional: Associate with specific documents
    documents = models.ManyToManyField(Document, blank=True, related_name='chat_sessions')
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title} ({self.created_at.strftime('%Y-%m-%d')})"
    
    def get_message_count(self):
        return self.messages.count()


class ChatMessage(models.Model):
    """Individual message in a chat session"""
    MESSAGE_TYPE_CHOICES = [
        ('human', 'Human'),
        ('ai', 'AI'),
        ('system', 'System'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Store sources for AI responses
    sources = models.JSONField(null=True, blank=True, help_text="Retrieved document sources")
    
    # Performance metrics
    retrieval_time = models.FloatField(null=True, blank=True, help_text="Time taken to retrieve documents (seconds)")
    generation_time = models.FloatField(null=True, blank=True, help_text="Time taken to generate response (seconds)")
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        preview = self.content[:50] + '...' if len(self.content) > 50 else self.content
        return f"{self.message_type}: {preview}"


class DocumentEmbedding(models.Model):
    """Track embedding status for documents"""
    INDEX_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='embedding')
    is_indexed = models.BooleanField(default=False)
    index_status = models.CharField(max_length=20, choices=INDEX_STATUS_CHOICES, default='pending')
    
    # Embedding metadata
    chunk_count = models.IntegerField(default=0, help_text="Number of chunks created")
    embedding_model = models.CharField(max_length=100, blank=True, help_text="Model used for embeddings")
    
    # Timestamps
    indexed_at = models.DateTimeField(null=True, blank=True)
    last_indexed_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.document.title} - {self.index_status}"
    
    def mark_processing(self):
        self.index_status = 'processing'
        self.save(update_fields=['index_status', 'updated_at'])
    
    def mark_completed(self, chunk_count, embedding_model):
        self.is_indexed = True
        self.index_status = 'completed'
        self.chunk_count = chunk_count
        self.embedding_model = embedding_model
        self.indexed_at = timezone.now()
        self.last_indexed_at = timezone.now()
        self.error_message = ''
        self.save()
    
    def mark_failed(self, error_message):
        self.index_status = 'failed'
        self.error_message = error_message
        self.retry_count += 1
        self.save()