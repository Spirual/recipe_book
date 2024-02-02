from rest_framework.permissions import (
    BasePermission,
    IsAuthenticatedOrReadOnly,
    SAFE_METHODS,
)


class IsAuthorOrReadOnlyPermission(IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.author == request.user


class AllowAnyExceptMe(BasePermission):
    def has_permission(self, request, view):
        return (
                '/users/me/' not in request.path or
                request.user.is_authenticated
        )
