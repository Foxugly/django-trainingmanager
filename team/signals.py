"""Signals that keep event.members in sync with TeamMembership state.

Strategy:
- A new active TeamMembership (left_at IS NULL) -> attach the member
  to all FUTURE events of the team.
- A TeamMembership update where left_at becomes non-NULL -> remove the
  member from all future events of the team.

"Future" is computed against `Event.date` which is a DateField (not
DateTimeField). We compare against `timezone.localdate()`. Events with
date IS NULL are skipped — without a date we cannot say "future" honestly.

Past events are never touched: attendance history is preserved.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import TeamMembership

logger = logging.getLogger(__name__)


@receiver(post_save, sender=TeamMembership)
def sync_event_members_on_membership_change(sender, instance, created, **kwargs):
    from event.models import Event

    today = timezone.localdate()
    team = instance.team
    member = instance.member

    future_events = Event.objects.filter(
        refer_program__team=team,
        date__gte=today,
    )

    if created and instance.left_at is None:
        for event in future_events:
            event.members.add(member)
        logger.info(
            "Auto-attached member %s to %d future events of team %s (membership created)",
            member.pk,
            future_events.count(),
            team.pk,
        )
        return

    if not created and instance.left_at is not None:
        for event in future_events:
            event.members.remove(member)
        logger.info(
            "Auto-detached member %s from %d future events of team %s (membership ended at %s)",
            member.pk,
            future_events.count(),
            team.pk,
            instance.left_at,
        )
