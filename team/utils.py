from django.db.models import Q

from .models import Team


def user_accessible_sport_language_pairs(user):
    """(sport_id, language) tuples for which the user has team membership.

    Membership = owner, manager, or athlete on an active team.
    Used to scope catalog reads by both sport AND language.
    """
    if not user.is_authenticated:
        return []
    teams = Team.objects.filter(
        Q(owner=user) | Q(managers=user) | Q(members__user=user),
        is_active=True,
    ).distinct()
    return list(teams.values_list("sport_id", "language").distinct())
