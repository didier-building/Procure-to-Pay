from rest_framework import permissions

class IsAuthenticatedAndHasProfile(permissions.BasePermission):
    """
    Ensures the user is authenticated and has a profile with a role attribute.
    We rely on view logic for specific role checks.
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and hasattr(user, 'profile'))
