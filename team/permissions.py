from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import SAFE_METHODS, BasePermission


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
        from team.models import Team

        return Team.objects.filter(
            Q(owner=request.user) | Q(managers=request.user),
            is_active=True,
        ).exists()


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
