# DocuVault - Document Management System with RAG Chatbot

A comprehensive Django-based Document Management System with role-based access control, version tracking, collaboration features, and an AI-powered RAG (Retrieval-Augmented Generation) chatbot for intelligent document querying.

## 🚀 Features

### 🤖 AI-Powered RAG Chatbot (NEW)
- **Intelligent Document Search**: Ask questions about your documents in natural language
- **Context-Aware Responses**: Uses Qwen2.5-7B LLM for accurate answers
- **Source Citations**: Shows which documents were used to generate answers
- **Conversation Memory**: Maintains chat history for contextual follow-ups
- **Document Indexing**: Automatic vectorization using Qwen3-Embedding-0.6B
- **GPU Acceleration**: CUDA support for fast inference
- **Permission-Aware**: Only searches documents you have access to

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
DocuVault/
├── config/                 # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── documents/              # Main Django app
│   ├── models.py           # Database models
│   ├── views.py            # View functions
│   ├── rag_views.py        # RAG chatbot views
│   ├── urls.py             # URL routing
│   ├── forms.py            # Form definitions
│   ├── admin.py            # Admin interface
│   ├── rag/                # RAG system modules
│   │   ├── config.py       # RAG configuration
│   │   ├── conversation.py # Main chatbot class
│   │   ├── embeddings.py   # Embedding generation
│   │   ├── vector_store.py # ChromaDB operations
│   │   ├── llm_manager.py  # LLM loading/inference
│   │   ├── retriever.py    # Query processing
│   │   └── document_processor.py # Document chunking
│   ├── templates/          # HTML templates
│   │   └── documents/
│   │       ├── chatbot.html
│   │       ├── auth/
│   │       └── ...
│   └── migrations/         # Database migrations
├── media/                  # User uploaded files
│   ├── documents/          # Document files
│   ├── avatars/            # User avatars
│   └── rag/                # RAG data
│       └── chroma_db/      # Vector database
├── static/                 # Static files (CSS, JS)
├── fix_dependencies.py     # Automated installer
├── test_rag.py             # RAG testing script
└── manage.py               # Django management
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

### RAG System Models
12. **ChatSession** - User chatbot sessions
13. **ChatMessage** - Individual chat messages with sources
14. **DocumentEmbedding** - Document indexing status and metadata

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

### Prerequisites
- Python 3.10+
- CUDA-capable GPU (optional, for RAG chatbot acceleration)
- 8GB+ RAM (16GB recommended for RAG features)

### Quick Setup

1. **Clone the repository**:
```bash
git clone https://github.com/ft-prince/DocuVault.git
cd DocuVault
```

2. **Create virtual environment**:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies** (Automated):
```bash
python fix_dependencies.py
```

Or manually:
```bash
pip install -r requirements.txt
pip install -r requirements_rag.txt
```

4. **Run migrations**:
```bash
python manage.py migrate
```

5. **Create superuser**:
```bash
python manage.py createsuperuser
```

6. **Run the development server**:
```bash
python manage.py runserver
```

7. **Access the application**:
- Main site: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin/
- RAG Chatbot: http://127.0.0.1:8000/chatbot/

### Windows Automated Setup
For Windows users, use the provided scripts:
```bash
# PowerShell
.\setup_windows.ps1

# Command Prompt
setup_windows.bat
```

## 🤖 RAG Chatbot Setup

The RAG chatbot uses the following models:
- **LLM**: Qwen/Qwen2.5-7B (8-bit quantized, ~7GB)
- **Embeddings**: Qwen/Qwen3-Embedding-0.6B (~2GB)
- **Vector DB**: ChromaDB (persistent storage)

### First-time Usage
1. Upload documents through the document management interface
2. Index documents by clicking the "Index for RAG" button on each document
3. Navigate to the chatbot page
4. Ask questions about your indexed documents

**Note**: First run will download models (~9GB total). Ensure stable internet connection.

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

## 🛠️ Technology Stack

- **Backend**: Django 4.2.26
- **Database**: SQLite (default) / PostgreSQL (production)
- **AI/ML**: 
  - LangChain 0.1.20
  - Transformers (HuggingFace)
  - Sentence-Transformers
  - PyTorch with CUDA support
- **Vector Database**: ChromaDB
- **Frontend**: HTML, CSS, JavaScript (vanilla)

## 📦 Project Files

- `fix_dependencies.py` - Automated dependency installer
- `test_rag.py` - RAG system testing script
- `setup_windows.bat` - Windows CMD setup script
- `setup_windows.ps1` - Windows PowerShell setup script
- `requirements.txt` - Core Django dependencies
- `requirements_rag.txt` - RAG/AI dependencies

## 🚦 Future Enhancements

- [ ] Multi-language support for RAG chatbot
- [ ] Document summarization
- [ ] Batch document indexing improvements
- [ ] Real-time collaboration using WebSockets
- [ ] Email notifications
- [ ] API endpoints (REST/GraphQL)
- [ ] Cloud storage integration (AWS S3, Google Drive)
- [ ] Advanced analytics and reporting
- [ ] Two-factor authentication

## 📄 License

This project is open source and available for educational and commercial use.

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


---

**Built with Django** 🚀