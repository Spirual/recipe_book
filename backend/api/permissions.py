from rest_framework.permissions import IsAuthenticatedOrReadOnly, SAFE_METHODS, \
    BasePermission


class IsAuthorOrReadOnlyPermission(IsAuthenticatedOrReadOnly):

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.author == request.user


class CurrentUserOrReadOnly(IsAuthenticatedOrReadOnly):

    def has_object_permission(self, request, view, obj):
        user = request.user
        if type(obj) == type(user) and obj == user:
            return True
        return request.method in SAFE_METHODS


class AllowAnyExceptMe(BasePermission):

    def has_permission(self, request, view):
        if '/users/me/' in request.path and not request.user.is_authenticated:
            return False
        return True
