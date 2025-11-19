# Document Management System (DMS)

A comprehensive Django-based Document Management System with role-based access control, version tracking, collaboration features, and advanced document management capabilities.

## 🚀 Features

### User Management & Authentication
- **Guest Users**: View public documents and create accounts
- **Regular Users**: Full document management capabilities
- **Admin Users**: Complete system administration
- **Role-Based Access Control (RBAC)**: Custom roles with hierarchical permission levels (1-100)
- Secure user authentication and authorization
- User profiles with avatars and detailed information

### Document Management
- **Upload & Storage**: Secure document upload with support for multiple file types
- **Access Control**: 
  - Public: Accessible to all users
  - Private: Only owner can access
  - Role-Based: Access based on user role level
  - Custom: Share with specific users
- **Version Control**: Track all document versions with change notes
- **Document Metadata**: 
  - Title, description, category, tags
  - File size and type tracking
  - View and download counters
- **Document Locking**: Prevent concurrent edits
- **Soft Delete**: Documents can be recovered

### Search & Discovery
- **Advanced Search**: Full-text search with multiple filters
- **Category Organization**: Hierarchical category system with colors and icons
- **Tag System**: Flexible tagging for better organization
- **Filtering**: By category, access level, owner, date range, etc.
- **Sorting**: Multiple sorting options (date, title, views, etc.)

### Collaboration Features
- **Comments & Replies**: Threaded comment system on documents
- **Document Sharing**: Share documents with specific users
- **Shareable Links**: Generate temporary links with optional:
  - Password protection
  - Expiration dates
  - Access count limits
- **Real-time Notifications**: Get notified about:
  - Document shares
  - Comments and replies
  - Permission changes
  - Mentions

### Additional Features
- **Favorites/Bookmarks**: Quick access to important documents
- **Activity Logging**: Complete audit trail of all actions
- **Dashboard**: Personalized overview with recent activities
- **Bulk Operations**: Upload multiple documents at once
- **File Preview**: Preview documents before downloading
- **Download Control**: Enable/disable downloads per document
- **User Profiles**: Detailed user profiles with activity history

## 📁 Project Structure

```
dms_project/
├── documents/
│   ├── models.py           # Database models
│   ├── views.py            # View functions
│   ├── urls.py             # URL routing
│   ├── forms.py            # Form definitions
│   ├── admin.py            # Admin interface configuration
│   ├── migrations/         # Database migrations
│   └── templates/          # HTML templates
│       └── documents/
│           ├── auth/       # Authentication templates
│           ├── admin/      # Admin templates
│           └── ...         # Other templates
├── media/                  # User uploaded files
│   ├── documents/          # Document files
│   ├── avatars/            # User avatars
│   └── document_versions/  # Version files
└── static/                 # Static files (CSS, JS, images)
```

## 🗄️ Database Models

### Core Models
1. **User** (Extended AbstractUser)
   - Custom user model with role assignment
   - User types: guest, user, admin
   - Additional fields: bio, avatar, phone, department

2. **Role**
   - Custom roles with hierarchical levels (1-100)
   - Cannot delete default roles
   - Track role assignment to users

3. **Document**
   - Main document storage
   - Multiple access levels
   - Version tracking
   - View/download counters
   - Lock mechanism

4. **Category**
   - Hierarchical categories
   - Color-coded organization
   - Icon support

5. **Tag**
   - Flexible tagging system
   - Many-to-many with documents

### Supporting Models
6. **DocumentVersion** - Version history tracking
7. **DocumentComment** - Comments with threading support
8. **SharedLink** - Temporary shareable links
9. **Favorite** - User bookmarks
10. **ActivityLog** - Complete audit trail
11. **Notification** - User notifications

## 🔐 Permission System

### User Types
- **Guest**: View public documents only
- **User**: Create, edit, delete own documents
- **Admin**: Full system access + user/role management

### Access Levels
1. **Public**: Anyone can view
2. **Private**: Only owner can view
3. **Role-Based**: Users with role level >= required level
4. **Custom**: Specific users granted access

### Role Hierarchy
- Roles have levels from 1-100
- Higher level = more privileges
- Admin users automatically have level 100
- Users can only access documents at or below their role level

## 🛣️ URL Structure

### Authentication
- `/register/` - User registration
- `/login/` - User login
- `/logout/` - User logout

### Main Pages
- `/` - Home page (public documents)
- `/dashboard/` - User dashboard

### Documents
- `/documents/` - List all documents
- `/documents/create/` - Create new document
- `/documents/<id>/` - View document details
- `/documents/<id>/edit/` - Edit document
- `/documents/<id>/delete/` - Delete document
- `/documents/<id>/download/` - Download document

### Comments
- `/documents/<id>/comments/create/` - Add comment
- `/comments/<id>/delete/` - Delete comment

### Favorites
- `/documents/<id>/favorite/` - Toggle favorite
- `/favorites/` - List favorites

### Sharing
- `/documents/<id>/share/` - Create shareable link
- `/share/<token>/` - Access via shared link

### Profile
- `/profile/` - View own profile
- `/profile/edit/` - Edit profile
- `/profile/<username>/` - View user profile

### Admin (Admin Only)
- `/admin/users/` - List all users
- `/admin/users/<id>/update-role/` - Update user role
- `/admin/roles/` - List all roles
- `/admin/roles/create/` - Create role
- `/admin/roles/<id>/edit/` - Edit role
- `/admin/roles/<id>/delete/` - Delete role

### Other
- `/categories/` - List categories
- `/notifications/` - View notifications
- `/search/` - Advanced search
- `/activity/` - Activity log

## 🎨 Forms

1. **UserRegistrationForm** - User signup
2. **UserLoginForm** - User login
3. **UserProfileForm** - Profile editing
4. **DocumentForm** - Document creation/editing with tags
5. **CategoryForm** - Category management
6. **RoleForm** - Role management
7. **CommentForm** - Comment creation
8. **SharedLinkForm** - Shareable link generation
9. **DocumentSearchForm** - Advanced search
10. **BulkUploadForm** - Multiple file upload

## 📊 Admin Interface Features

- Custom admin interface for all models
- Inline editing for versions and comments
- Bulk actions for notifications
- Read-only activity logs
- User statistics and counters
- Filterable and searchable lists
- Custom display fields with formatting

## 🔧 Installation & Setup

1. **Install Django and dependencies**:
```bash
pip install django pillow
```

2. **Create migrations**:
```bash
python manage.py makemigrations documents
python manage.py migrate
```

3. **Create superuser**:
```bash
python manage.py createsuperuser
```

4. **Create default roles** (in Django shell):
```python
from documents.models import Role

# Create basic roles
Role.objects.create(name='Viewer', level=10, is_default=True, description='Can view basic documents')
Role.objects.create(name='Editor', level=30, description='Can create and edit documents')
Role.objects.create(name='Manager', level=50, description='Can manage team documents')
Role.objects.create(name='Admin', level=100, is_default=True, description='Full access')
```

5. **Run the development server**:
```bash
python manage.py runserver
```

## 📝 Usage Examples

### Creating a Document
```python
from documents.models import Document, User

owner = User.objects.get(username='john')
doc = Document.objects.create(
    title='Project Proposal',
    description='Q4 2024 Project Proposal',
    file='path/to/file.pdf',
    owner=owner,
    access_level='role',
    required_role_level=30
)
```

### Checking Permissions
```python
# Check if user can view document
if document.can_view(user):
    # Show document
    
# Check if user can edit
if document.can_edit(user):
    # Allow editing
```

### Creating Shareable Link
```python
from documents.models import SharedLink
from datetime import timedelta
from django.utils import timezone

link = SharedLink.objects.create(
    document=document,
    created_by=user,
    expires_at=timezone.now() + timedelta(days=7),
    max_access_count=10,
    password='secret123',
    allow_download=True
)
```

### Logging Activity
```python
from documents.models import ActivityLog

ActivityLog.objects.create(
    user=request.user,
    document=document,
    action='view',
    description=f'Viewed document: {document.title}',
    ip_address=request.META.get('REMOTE_ADDR')
)
```

## 🔒 Security Features

- Password hashing with Django's built-in system
- CSRF protection on all forms
- File upload validation and size limits (100MB default)
- SQL injection protection via ORM
- XSS protection through template escaping
- Permission checks on all sensitive operations
- Activity logging for audit trails
- Soft delete to prevent accidental data loss

## 🚦 Future Enhancements

- [ ] Full-text search using Elasticsearch
- [ ] Real-time collaboration using WebSockets
- [ ] OCR for scanned documents
- [ ] Advanced file preview (PDF, Office docs)
- [ ] Email notifications
- [ ] Document templates
- [ ] Workflow automation
- [ ] API endpoints (REST/GraphQL)
- [ ] Mobile app integration
- [ ] Cloud storage integration (AWS S3, Google Drive)
- [ ] Advanced analytics and reporting
- [ ] Document encryption at rest
- [ ] Two-factor authentication

## 📄 License

This project is open source and available for educational and commercial use.

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


---

**Built with Django** 🚀