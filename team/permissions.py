from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS, BasePermission

from .queries import managed_teams


class OwnerOnlyDeleteDenied(PermissionDenied):
    """Raised when a non-owner (e.g. a manager) tries to DELETE a team.

    The dedicated default_code lets the frontend match this case
    distinctly from a generic 'permission_denied'.
    """

    default_detail = _("Only the team owner can delete the team.")
    default_code = "owner_only_delete"


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
    SAFE_METHODS for any authenticated user; mutations for owner or
    managers — except DELETE which is reserved to the owner.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.method == "DELETE":
            if obj.owner_id != request.user.pk:
                raise OwnerOnlyDeleteDenied()
            return True
        return obj.is_managed_by(request.user)


class IsTrainer(BasePermission):
    """
    Read access for any authenticated user.
    Write access requires owning or managing at least one active team.
    """

    message = _("Only trainers (owners or managers of an active team) can modify the catalog.")

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return managed_teams(request.user).filter(is_active=True).exists()


class IsJoinRequestParticipant(BasePermission):
    """
    Object-level permission for TeamJoinRequest:
    - the requester (obj.user)
    - the team owner or any team manager
    """

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        if obj.user_id == request.user.pk:
            return True
        return obj.team.is_managed_by(request.user)
