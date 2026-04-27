from django.db.models import Q

from .models import Team


def user_accessible_sport_ids(user):
    """IDs of sports for which the user has any membership in an active team.

    Membership = owner, manager, or athlete (via Member.teams).
    Used to scope read access on the shared catalog (Exercise, Round).
    """
    if not user.is_authenticated:
        return []
    teams = Team.objects.filter(
        Q(owner=user) | Q(managers=user) | Q(members__user=user),
        is_active=True,
    ).distinct()
    return list(teams.values_list("sport_id", flat=True).distinct())
