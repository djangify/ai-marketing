# ai_marketing/middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

# ai_marketing/middleware.py

class AuthRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Public paths that don't require authentication
        self.public_paths = [
            '/',
            '/accounts/login/',
            '/accounts/signup/',
            '/pricing/',
            '/blog/',
        ]
        # Admin paths will be handled separately
    
    def __call__(self, request):
        # Check if the path requires authentication
        path = request.path
        
        # Allow all admin paths
        if path.startswith('/admin/'):
            return self.get_response(request)
            
        # Allow all public paths and paths that start with them
        if any(path == public_path or path.startswith(public_path + 'media/') or 
               path.startswith(public_path + 'static/') for public_path in self.public_paths):
            return self.get_response(request)
        
        # For non-public paths, check if the user is authenticated
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in to access this page.")
            return redirect(f"{reverse('accounts:login')}?next={path}")
        
        return self.get_response(request)