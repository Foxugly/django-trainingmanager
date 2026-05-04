from django.db.models import Q

from .models import Team


def user_visible_teams(user):
    """Teams the user can see (read).

    A team is visible to:
    - its owner
    - any of its managers
    - any of its current active members (TeamMembership.left_at IS NULL)
    - any authenticated user, when the team is public AND active

    Owners and managers also see their inactive (soft-deleted) teams,
    so they can reactivate or hard-delete them. Members never see
    inactive teams via this helper.
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
