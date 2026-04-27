from rest_framework.permissions import SAFE_METHODS, BasePermission


class CanManageProgram(BasePermission):
    """SAFE_METHODS for any authenticated reader; mutations for owner/manager."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.team.is_managed_by(request.user)
