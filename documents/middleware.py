from django.shortcuts import redirect
from django.urls import reverse

EXEMPT_URLS = {
    'login', 'logout', 'register', 'pending_approval', 'approval_status_api', 'home',
}


class ApprovalRequiredMiddleware:
    """
    Redirect authenticated-but-unapproved users to the pending approval page
    for every request except the exempt URLs and static/media files.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_approved \
                and request.user.email != 'admin@dms.local':
            path = request.path_info
            # Allow static/media files through
            if path.startswith('/static/') or path.startswith('/media/'):
                return self.get_response(request)
            # Allow Django admin through (superusers are always approved conceptually)
            if path.startswith('/django-admin/'):
                return self.get_response(request)
            # Allow exempt named URLs
            pending_url = reverse('pending_approval')
            status_url = reverse('approval_status_api')
            login_url = reverse('login')
            logout_url = reverse('logout')
            register_url = reverse('register')
            home_url = reverse('home')
            exempt_paths = {pending_url, status_url, login_url, logout_url, register_url, home_url}
            if path not in exempt_paths:
                return redirect('pending_approval')
        return self.get_response(request)
