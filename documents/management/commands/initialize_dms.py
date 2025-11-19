"""
Management command to initialize the Document Management System with default data
Usage: python manage.py initialize_dms
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from documents.models import Role, Category

User = get_user_model()


class Command(BaseCommand):
    help = 'Initialize the Document Management System with default roles and categories'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Initializing Document Management System...'))
        
        # Create default roles
        self.stdout.write('Creating default roles...')
        roles_data = [
            {
                'name': 'Viewer',
                'level': 10,
                'is_default': True,
                'description': 'Basic viewing permissions. Can view public and role-appropriate documents.'
            },
            {
                'name': 'Contributor',
                'level': 25,
                'is_default': False,
                'description': 'Can create and manage own documents, view documents up to level 25.'
            },
            {
                'name': 'Editor',
                'level': 40,
                'is_default': False,
                'description': 'Can create, edit, and manage documents. Access to documents up to level 40.'
            },
            {
                'name': 'Manager',
                'level': 60,
                'is_default': False,
                'description': 'Team management permissions. Can manage team documents and access up to level 60.'
            },
            {
                'name': 'Senior Manager',
                'level': 80,
                'is_default': False,
                'description': 'Department-level permissions. Access to sensitive documents up to level 80.'
            },
            {
                'name': 'Administrator',
                'level': 100,
                'is_default': True,
                'description': 'Full system access. Can manage all documents, users, and system settings.'
            },
        ]
        
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'level': role_data['level'],
                    'is_default': role_data['is_default'],
                    'description': role_data['description']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created role: {role.name} (Level {role.level})'))
            else:
                self.stdout.write(f'  - Role already exists: {role.name}')
        
        # Create default categories
        self.stdout.write('\nCreating default categories...')
        categories_data = [
            {
                'name': 'General',
                'description': 'General documents and files',
                'color': '#6c757d',
                'icon': 'fa-file'
            },
            {
                'name': 'Financial',
                'description': 'Financial reports, invoices, and budgets',
                'color': '#28a745',
                'icon': 'fa-dollar-sign'
            },
            {
                'name': 'Human Resources',
                'description': 'HR documents, policies, and employee information',
                'color': '#007bff',
                'icon': 'fa-users'
            },
            {
                'name': 'Legal',
                'description': 'Legal documents, contracts, and agreements',
                'color': '#dc3545',
                'icon': 'fa-gavel'
            },
            {
                'name': 'Marketing',
                'description': 'Marketing materials, campaigns, and analytics',
                'color': '#fd7e14',
                'icon': 'fa-bullhorn'
            },
            {
                'name': 'Technical',
                'description': 'Technical documentation and specifications',
                'color': '#20c997',
                'icon': 'fa-code'
            },
            {
                'name': 'Projects',
                'description': 'Project documentation and deliverables',
                'color': '#17a2b8',
                'icon': 'fa-project-diagram'
            },
            {
                'name': 'Reports',
                'description': 'Reports and analytics',
                'color': '#6f42c1',
                'icon': 'fa-chart-bar'
            },
            {
                'name': 'Presentations',
                'description': 'Presentation files and slides',
                'color': '#e83e8c',
                'icon': 'fa-presentation'
            },
            {
                'name': 'Archives',
                'description': 'Archived and historical documents',
                'color': '#6c757d',
                'icon': 'fa-archive'
            },
        ]
        
        # Check if admin user exists
        admin_user = User.objects.filter(user_type='admin').first()
        
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'color': cat_data['color'],
                    'icon': cat_data['icon'],
                    'created_by': admin_user
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created category: {category.name}'))
            else:
                self.stdout.write(f'  - Category already exists: {category.name}')
        
        # Create demo admin user if no admin exists
        if not User.objects.filter(user_type='admin').exists():
            self.stdout.write('\nNo admin user found. Creating demo admin user...')
            admin_role = Role.objects.get(name='Administrator')
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@dms.local',
                password='admin123',
                user_type='admin',
                role=admin_role,
                first_name='System',
                last_name='Administrator'
            )
            self.stdout.write(self.style.SUCCESS(f'  ✓ Created admin user: {admin_user.username}'))
            self.stdout.write(self.style.WARNING('  ⚠ Default password: admin123 (CHANGE THIS!)'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ Initialization complete!'))
        self.stdout.write('\nNext steps:')
        self.stdout.write('  1. Create a superuser: python manage.py createsuperuser')
        self.stdout.write('  2. Run the development server: python manage.py runserver')
        self.stdout.write('  3. Access the admin panel: http://localhost:8000/admin/')
        self.stdout.write('  4. Access the app: http://localhost:8000/')