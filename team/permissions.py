from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsTeamOwnerOrReadOnly(BasePermission):
    """
    SAFE_METHODS for any authenticated user; mutations only for owner.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.owner_id == request.user.pk


class IsTeamManagerOrReadOnly(BasePermission):
    """
    SAFE_METHODS for any authenticated user; mutations for owner or managers.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.is_managed_by(request.user)
