from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsTeamMemberAndChatPolicy(BasePermission):
    """Permission for team chat messages.

    Read (SAFE_METHODS): any team member (owner, manager, athlete linked
    via Member.user).

    Write:
      - create: gated by team.chat_mode
        * 'all'           -> any team member
        * 'coaches_only'  -> only owner/managers
      - update / delete: author of the message OR team owner/manager

    The view must implement get_team() so this permission can resolve
    the URL context.
    """

    message = _("You don't have permission to access this team's chat.")

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        team = view.get_team()
        if team is None:
            return False

        user = request.user
        is_coach = team.is_managed_by(user)
        is_athlete_member = team.memberships.filter(
            member__user_id=user.pk, left_at__isnull=True
        ).exists()
        if not (is_coach or is_athlete_member):
            return False

        if request.method in SAFE_METHODS:
            return True

        # POST (create)
        if getattr(view, "action", None) == "create":
            if team.chat_mode == "all":
                return True
            return is_coach

        # PATCH / PUT / DELETE -> object-level check decides
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        team = view.get_team()
        if obj.author_id == request.user.pk:
            return True
        if team is not None and team.is_managed_by(request.user):
            return True
        return False
