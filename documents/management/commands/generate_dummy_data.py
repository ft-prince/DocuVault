"""
Django Management Command to Generate Dummy Data
Usage: python manage.py generate_dummy_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.base import ContentFile
import random
import string
from datetime import timedelta
from documents.models import (
    User, Role, Category, Tag, Document, DocumentVersion,
    DocumentComment, SharedLink, Favorite, ActivityLog, Notification
)


class Command(BaseCommand):
    help = 'Generate realistic dummy data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of users to create'
        )
        parser.add_argument(
            '--documents',
            type=int,
            default=50,
            help='Number of documents to create'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating'
        )

    def handle(self, *args, **options):
        num_users = options['users']
        num_documents = options['documents']
        clear_data = options['clear']

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('GENERATING DUMMY DATA'))
        self.stdout.write(self.style.SUCCESS('=' * 80))

        # Clear data if requested
        if clear_data:
            self.stdout.write('\n⚠️  Clearing existing data...')
            self._clear_all_data()
            self.stdout.write(self.style.SUCCESS('✓ Existing data cleared'))

        # Sample data
        first_names = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']
        departments = ['Engineering', 'Sales', 'Marketing', 'HR', 'Finance', 'Operations']

        # Create roles
        self.stdout.write('\n📝 Creating roles...')
        viewer_role, _ = Role.objects.get_or_create(
            name='Viewer',
            defaults={'level': 10, 'description': 'Basic viewing'}
        )
        editor_role, _ = Role.objects.get_or_create(
            name='Editor',
            defaults={'level': 40, 'description': 'Can edit'}
        )
        manager_role, _ = Role.objects.get_or_create(
            name='Manager',
            defaults={'level': 60, 'description': 'Team management'}
        )
        roles = [viewer_role, editor_role, manager_role]
        self.stdout.write(self.style.SUCCESS('✓ Roles ready'))

        # Create users
        self.stdout.write(f'\n👥 Creating {num_users} users...')
        users = []
        for i in range(num_users):
            username = f"{random.choice(first_names).lower()}.{random.choice(last_names).lower()}{i}"
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                continue
            
            user = User.objects.create_user(
                username=username,
                email=f"{username}@example.com",
                password='password123',
                first_name=random.choice(first_names),
                last_name=random.choice(last_names),
                user_type='admin' if i < 2 else 'user',
                role=random.choice(roles),
                department=random.choice(departments)
            )
            users.append(user)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(users)} users'))

        # If no users were created (all existed), get existing users
        if not users:
            users = list(User.objects.all()[:num_users])
            self.stdout.write(self.style.WARNING(f'ℹ️  Using {len(users)} existing users'))

        # Create categories using get_or_create
        self.stdout.write('\n📁 Creating categories...')
        categories = []
        category_data = [
            ('General', 'General documents', '#6c757d'),
            ('Financial', 'Financial documents', '#28a745'),
            ('HR', 'HR documents', '#ffc107'),
            ('Legal', 'Legal documents', '#dc3545'),
            ('Marketing', 'Marketing documents', '#17a2b8'),
            ('Technical', 'Technical documents', '#6f42c1'),
        ]
        
        for name, description, color in category_data:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'color': color,
                    'created_by': random.choice(users)
                }
            )
            categories.append(category)
            if created:
                self.stdout.write(f'  ✓ Created category: {name}')
            else:
                self.stdout.write(f'  ℹ️  Category already exists: {name}')
        
        self.stdout.write(self.style.SUCCESS(f'✓ {len(categories)} categories ready'))

        # Create tags using get_or_create
        self.stdout.write('\n🏷️  Creating tags...')
        tag_names = ['important', 'urgent', 'draft', 'final', 'review', 'approved']
        tags = []
        for name in tag_names:
            tag, created = Tag.objects.get_or_create(name=name)
            tags.append(tag)
            if created:
                self.stdout.write(f'  ✓ Created tag: {name}')
            else:
                self.stdout.write(f'  ℹ️  Tag already exists: {name}')
        
        self.stdout.write(self.style.SUCCESS(f'✓ {len(tags)} tags ready'))

        # Create documents
        self.stdout.write(f'\n📄 Creating {num_documents} documents...')
        documents = []
        for i in range(num_documents):
            owner = random.choice(users)
            title = f"Document {i+1} - {random.choice(['Report', 'Proposal', 'Analysis', 'Guide'])}"
            content = f"Sample document content for {title}\n\n" + "Lorem ipsum dolor sit amet. " * 50
            
            doc = Document.objects.create(
                title=title,
                description=f"This is a test document about {random.choice(['finance', 'operations', 'strategy'])}",
                file=ContentFile(content.encode('utf-8'), name=f'doc_{i}.txt'),
                owner=owner,
                category=random.choice(categories),
                access_level=random.choice(['public', 'private', 'role']),
                file_size=len(content),
                file_type='text/plain',
                views_count=random.randint(0, 100),
                downloads_count=random.randint(0, 50)
            )
            doc.tags.set(random.sample(tags, k=random.randint(1, 3)))
            documents.append(doc)

            # Create version
            DocumentVersion.objects.create(
                document=doc,
                version_number=1,
                file=doc.file,
                file_size=doc.file_size,
                uploaded_by=owner,
                change_note="Initial version"
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(documents)} documents'))

        # Create comments
        self.stdout.write('\n💬 Creating comments...')
        comments = []
        comment_texts = [
            'Great work!',
            'Thanks for sharing.',
            'Please review this section.',
            'Looks good to me.',
            'Can we discuss this further?',
            'Approved!',
            'Minor changes needed.',
            'Excellent documentation.'
        ]
        
        for _ in range(30):
            doc = random.choice(documents)
            comment = DocumentComment.objects.create(
                document=doc,
                user=random.choice(users),
                content=random.choice(comment_texts)
            )
            comments.append(comment)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(comments)} comments'))

        # Create favorites
        self.stdout.write('\n⭐ Creating favorites...')
        favorites = []
        for _ in range(20):
            user = random.choice(users)
            doc = random.choice(documents)
            if not Favorite.objects.filter(user=user, document=doc).exists():
                fav = Favorite.objects.create(user=user, document=doc)
                favorites.append(fav)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(favorites)} favorites'))

        # Create activity logs
        self.stdout.write('\n📊 Creating activity logs...')
        action_types = ['create', 'view', 'download', 'edit', 'share']
        activity_count = 0
        
        for doc in documents[:20]:
            # Create log
            ActivityLog.objects.create(
                user=doc.owner,
                document=doc,
                action='create',
                description=f'Created document: {doc.title}',
                ip_address='127.0.0.1'
            )
            activity_count += 1
            
            # Add some random activities
            for _ in range(random.randint(1, 3)):
                ActivityLog.objects.create(
                    user=random.choice(users),
                    document=doc,
                    action=random.choice(action_types),
                    description=f'{random.choice(action_types).capitalize()} action on: {doc.title}',
                    ip_address='127.0.0.1'
                )
                activity_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {activity_count} activity logs'))

        # Summary
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('✅ DUMMY DATA GENERATION COMPLETE!'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'\nCreated:')
        self.stdout.write(f'  👥 {len(users)} Users')
        self.stdout.write(f'  📁 {len(categories)} Categories')
        self.stdout.write(f'  🏷️  {len(tags)} Tags')
        self.stdout.write(f'  📄 {len(documents)} Documents')
        self.stdout.write(f'  💬 {len(comments)} Comments')
        self.stdout.write(f'  ⭐ {len(favorites)} Favorites')
        self.stdout.write(f'  📊 {activity_count} Activity Logs')
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write('All users have password: password123')
        self.stdout.write('=' * 80)

    def _clear_all_data(self):
        """Clear all data from database"""
        try:
            ActivityLog.objects.all().delete()
            self.stdout.write('  ✓ Cleared activity logs')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠️  {e}'))

        try:
            Notification.objects.all().delete()
            self.stdout.write('  ✓ Cleared notifications')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠️  {e}'))

        try:
            Favorite.objects.all().delete()
            self.stdout.write('  ✓ Cleared favorites')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠️  {e}'))

        try:
            SharedLink.objects.all().delete()
            self.stdout.write('  ✓ Cleared shared links')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠️  {e}'))

        try:
            DocumentComment.objects.all().delete()
            self.stdout.write('  ✓ Cleared comments')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠️  {e}'))

        try:
            DocumentVersion.objects.all().delete()
            self.stdout.write('  ✓ Cleared document versions')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠️  {e}'))

        try:
            Document.objects.all().delete()
            self.stdout.write('  ✓ Cleared documents')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠️  {e}'))

        try:
            Tag.objects.all().delete()
            self.stdout.write('  ✓ Cleared tags')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠️  {e}'))

        try:
            Category.objects.all().delete()
            self.stdout.write('  ✓ Cleared categories')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠️  {e}'))

        try:
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write('  ✓ Cleared non-superuser users')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠️  {e}'))