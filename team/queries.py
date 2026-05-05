from django.db.models import Q

from .models import Team


def user_member_teams(user):
    """Teams the user is a strict member of: owner, manager, or active
    TeamMembership. Does NOT include discoverable public teams.

    Use this for read-scoping of team-internal resources (Programs, Events,
    Members, Notes, Attendance, Chat, ...). A user must have an explicit
    link to the team — discovering a public team via /teams/ does not
    grant access to its content.

    Owners and managers also see their inactive (soft-deleted) teams.
    Active members only see active teams.
    """
    if not user.is_authenticated:
        return Team.objects.none()
    return Team.objects.filter(
        Q(owner=user)
        | Q(managers=user)
        | Q(
            memberships__member__user=user,
            memberships__left_at__isnull=True,
            is_active=True,
        ),
    ).distinct()


def user_visible_teams(user):
    """Teams the user can SEE in /teams/. Strictly broader than
    user_member_teams: adds public+active teams so an authenticated user
    can discover them and request to join via TeamJoinRequest.

    DO NOT use this helper for read-scoping team-internal resources
    (Programs/Events/Members/Notes/...): use user_member_teams instead.
    The discoverability is a Team-list affordance, not a content access
    grant.
    """
    if not user.is_authenticated:
        return Team.objects.none()
    return Team.objects.filter(
        Q(owner=user)
        | Q(managers=user)
        | Q(
            memberships__member__user=user,
            memberships__left_at__isnull=True,
            is_active=True,
        )
        | Q(is_public=True, is_active=True),
    ).distinct()


def managed_teams(user):
    """Teams the user can write to: owned + managed."""
    if not user.is_authenticated:
        return Team.objects.none()
    return Team.objects.filter(Q(owner=user) | Q(managers=user)).distinct()
