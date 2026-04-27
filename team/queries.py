from django.db.models import Q

from .models import Team


def accessible_teams(user):
    """Teams the user can see (read): owned + managed + public-active."""
    if not user.is_authenticated:
        return Team.objects.none()
    return Team.objects.filter(
        Q(owner=user) | Q(managers=user) | Q(is_public=True, is_active=True)
    ).distinct()


def managed_teams(user):
    """Teams the user can write to: owned + managed."""
    if not user.is_authenticated:
        return Team.objects.none()
    return Team.objects.filter(Q(owner=user) | Q(managers=user)).distinct()
