"""Signals that bootstrap event.members on Event creation.

When a new Event is created, attach all currently-active members of
the parent team (resolved via Event.refer_program.team).
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Event

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Event)
def auto_attach_active_members_on_event_create(sender, instance, created, **kwargs):
    if not created:
        return

    program = instance.refer_program
    if program is None:
        return

    team = program.team
    if team is None:
        return

    from team.models import TeamMembership

    active_member_ids = list(
        TeamMembership.objects.filter(
            team=team,
            left_at__isnull=True,
        ).values_list("member_id", flat=True)
    )
    if not active_member_ids:
        return

    instance.members.add(*active_member_ids)
    logger.info(
        "Auto-attached %d active members to new event %s (team %s)",
        len(active_member_ids),
        instance.pk,
        team.pk,
    )
