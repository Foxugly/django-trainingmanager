# Create your models here.
from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from event.models import Event
from member.models import Member
from tools.generic_class import GenericClass


# Create your models here.
class Agenda(GenericClass):
    name = models.CharField(max_length=100, verbose_name=_("name"))
    date_start = models.DateField(blank=True, null=True, )
    date_end = models.DateField(blank=True, null=True, )
    events = models.ManyToManyField(Event, blank=True, )
    members = models.ManyToManyField(Member, blank=True, )

    def get_members(self):
        return self.members.all()

    def __str__(self):
        return self.name

    # def get_add_class(self):
    #    return "agenda_add"

    # def get_add_url(self):
    #    return '#'

    def get_json_url(self):
        return reverse_lazy('agenda:events_json', kwargs={'agenda_id': self.pk})

    def get_events(self):
        return self.events.all()

    class Meta:
        verbose_name = _('Agenda    ')
