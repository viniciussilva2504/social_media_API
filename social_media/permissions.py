from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission: only the owner can edit/delete.
    Expects the object to have an `author` or `user` attribute.
    """

    owner_field = "author"

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        owner = getattr(obj, self.owner_field, None)
        if owner is None:
            owner = getattr(obj, "user", None)
        return owner == request.user


class IsProfileOwner(permissions.BasePermission):
    """
    Object-level permission for Profile objects.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user
