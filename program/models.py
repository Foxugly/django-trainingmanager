from django.db import models
from django.utils.translation import gettext as _

from event.models import Event
from member.models import Member
from tools.generic_class import GenericClass


class Program(GenericClass):
    name = models.CharField(max_length=100, verbose_name=_("name"))
    date_start = models.DateField(blank=True, null=True, )
    date_end = models.DateField(blank=True, null=True, )
    events = models.ManyToManyField(Event, blank=True, )
    members = models.ManyToManyField(Member, blank=True, )
    team = models.ForeignKey(
        'team.Team',
        on_delete=models.PROTECT,
        related_name='programs',
    )
    frequency_per_week = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True, default='')
    generated_by_ai = models.BooleanField(default=False)
    ai_prompt = models.TextField(blank=True, default='')
    ai_response = models.TextField(blank=True, default='')
    ai_generated_at = models.DateTimeField(null=True, blank=True)

    def get_members(self):
        return self.members.all()

    def __str__(self):
        return self.name

    def get_events(self):
        return self.events.all()

    class Meta:
        verbose_name = _('Program')
