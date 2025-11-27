from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User, Document, Category, Role, DocumentComment, SharedLink, Tag
import datetime


class UserRegistrationForm(UserCreationForm):
    """User registration form"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email address'
    }))
    first_name = forms.CharField(required=True, max_length=150, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First name'
    }))
    last_name = forms.CharField(required=True, max_length=150, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last name'
    }))

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email


class UserLoginForm(forms.Form):
    """User login form"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )


class UserProfileForm(forms.ModelForm):
    """User profile edit form"""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'bio', 'avatar', 'phone', 'department')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email address'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about yourself'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Department'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }


class DocumentForm(forms.ModelForm):
    """Document creation and edit form"""
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter tags separated by commas (e.g., finance, report, 2024)'
        }),
        help_text='Enter tags separated by commas'
    )
    
    change_note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Describe what changed in this version (optional)'
        }),
        help_text='Describe changes made in this version'
    )

    class Meta:
        model = Document
        fields = (
            'title', 'description', 'file', 'category', 'access_level',
            'required_role_level', 'shared_with', 'allow_comments', 'allow_download'
        )
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Document title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Document description'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'access_level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'required_role_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 100
            }),
            'shared_with': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 5
            }),
            'allow_comments': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'allow_download': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter shared_with to exclude current user
        if self.user:
            self.fields['shared_with'].queryset = User.objects.exclude(id=self.user.id)
        
        # Pre-populate tags if editing
        if self.instance and self.instance.pk:
            tags = self.instance.tags.all()
            self.fields['tags'].initial = ', '.join([tag.name for tag in tags])

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Limit file size to 100MB
            if file.size > 100 * 1024 * 1024:
                raise ValidationError("File size cannot exceed 100MB.")
        return file

    def clean_tags(self):
        tags_str = self.cleaned_data.get('tags', '')
        if tags_str:
            # Split by comma and clean up
            tag_names = [name.strip() for name in tags_str.split(',') if name.strip()]
            return tag_names
        return []

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
            
            # Handle tags
            tags_list = self.cleaned_data.get('tags', [])
            if tags_list:
                # Clear existing tags
                instance.tags.clear()
                
                # Create or get tags and add to document
                for tag_name in tags_list:
                    tag, created = Tag.objects.get_or_create(name=tag_name.lower())
                    instance.tags.add(tag)
            
            self.save_m2m()
        
        return instance


class CategoryForm(forms.ModelForm):
    """Category creation and edit form"""
    class Meta:
        model = Category
        fields = ('name', 'description', 'color', 'icon', 'parent')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Category description'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#007bff'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Icon class (e.g., fa-folder)'
            }),
            'parent': forms.Select(attrs={
                'class': 'form-select'
            }),
        }


class RoleForm(forms.ModelForm):
    """Role creation and edit form"""
    class Meta:
        model = Role
        fields = ('name', 'description', 'level', 'is_default')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Role name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Role description'
            }),
            'level': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 100,
                'value': 1
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_level(self):
        level = self.cleaned_data.get('level')
        if level < 1 or level > 100:
            raise ValidationError("Level must be between 1 and 100.")
        return level


class CommentForm(forms.ModelForm):
    """Comment form"""
    class Meta:
        model = DocumentComment
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write your comment here...'
            }),
        }


class SharedLinkForm(forms.ModelForm):
    """Shared link creation form"""
    expires_in_days = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=365,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Number of days until expiration'
        }),
        help_text='Leave empty for no expiration'
    )

    class Meta:
        model = SharedLink
        fields = ('password', 'max_access_count', 'allow_download')
        widgets = {
            'password': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional password protection'
            }),
            'max_access_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Maximum number of accesses',
                'min': 1
            }),
            'allow_download': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set expiration date if specified
        expires_in_days = self.cleaned_data.get('expires_in_days')
        if expires_in_days:
            from django.utils import timezone
            instance.expires_at = timezone.now() + datetime.timedelta(days=expires_in_days)
        
        if commit:
            instance.save()
        
        return instance


class DocumentSearchForm(forms.Form):
    """Advanced search form"""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search documents...'
        })
    )
    
    category = forms.ModelChoiceField(
        required=False,
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    access_level = forms.ChoiceField(
        required=False,
        choices=[('', 'All Access Levels')] + Document.ACCESS_LEVEL_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    owner = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class BulkUploadForm(forms.Form):
    """Bulk document upload form"""
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        }),
        help_text='Select a file to upload (upload one at a time or handle multiple in view)'
    )
    
    category = forms.ModelChoiceField(
        required=False,
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    access_level = forms.ChoiceField(
        choices=Document.ACCESS_LEVEL_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tags (comma-separated)'
        })
    )


# ============================================================
# RAG CHATBOT FORMS
# ============================================================

class ChatQueryForm(forms.Form):
    """Form for chatbot queries"""
    query = forms.CharField(
        max_length=1000,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Ask a question about your documents...',
            'rows': 3
        })
    )


class DocumentIndexForm(forms.Form):
    """Form for bulk document indexing"""
    force_reindex = forms.BooleanField(
        required=False,
        initial=False,
        label='Force re-index already indexed documents',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )