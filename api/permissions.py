from rest_framework import permissions
from django.conf import settings

class ServerAPIPermission(permissions.BasePermission):
    """
    Custom permission to allow access only if the correct API key is provided
    """
    def has_permission(self, request, view):
        # Check if the request contains the correct API key in the Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            return token == settings.SERVER_API_KEY
        return False