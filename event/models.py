from django.db import models
from django.utils.translation import gettext as _

from member.models import Member
from round.models import Round
from tools.generic_class import GenericClass


# Create your models here.
class Event(GenericClass):
    name = models.CharField(max_length=100, verbose_name=_("name"))
    goal = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("goal"))
    color = models.CharField(max_length=10, blank=True, verbose_name=_("color"))
    date = models.DateField(blank=True, null=True, )
    hour_start = models.TimeField(blank=True, null=True, )
    hour_end = models.TimeField(blank=True, null=True, )
    total = models.PositiveIntegerField(default=0)
    rounds = models.ManyToManyField(Round, blank=True, )
    members = models.ManyToManyField(Member, blank=True, )
    refer_agenda = models.ForeignKey('agenda.Agenda', verbose_name=_('refer_agenda'), related_name='back_agenda',
                                     null=True, on_delete=models.CASCADE)

    def __str__(self):
        return "%s %d" % (_('Event'), self.pk)

    def get_members_present(self):
        return self.members.all()

    def get_nb_members_present(self):
        return len(self.get_members_present())

    def get_all_members(self):
        return self.refer_agenda.members.all()

    def get_nb_all_members(self):
        return len(self.get_all_members())

    @staticmethod
    def hour_t(t):
        return t.strftime('%H:%M:%S')

    def start_t(self):
        return self.date.strftime('%Y-%m-%d') + "T" + self.hour_t(self.hour_start)

    def end_t(self):
        return self.date.strftime('%Y-%m-%d') + "T" + self.hour_t(self.hour_end)

    def as_json(self):
        return dict(id=str(self.id), start=self.start_t(), end=self.end_t(), title=self.name, color=self.color,
                    url=self.get_absolute_url())

    def get_rounds(self):
        return self.rounds.all().order_by("order")

    def get_table(self):
        out = "<table class='card-table table mb-0 table-bordered'>"
        out += "<thead><tr><th>#</th><th>Dist.</th><th>Round</th><th>Ex.</th><th></th></tr></head><tbody>"
        for r in self.get_rounds():
            out += r.get_row(True)
        out += "</tbody></table>"
        return out

    def get_table_raw(self):
        out = "<table class='table mb-0'>"
        out += "<thead><tr><th>#</th><th>Dist.</th><th>Round</th><th>Exercices</th></tr></thead><tbody>"
        for r in self.get_rounds():
            out += r.get_row(False)
        out += "</tbody></table>"
        return out

    def get_title_raw(self):
        out = "<table class='table'>"
        out += "<thead><tr><th class='text-center' colspan=2>%s</th></tr></thead>" % self.refer_agenda
        out += "<tbody><tr><td class='text-center'>Date : %s</td><td class='text-center'>Heure : %s </td></tr>" \
               "<tr><td class='text-center' colspan=2>Distance : %s m</td></tr></tbody></table>" % (
                   self.date.strftime('%d/%m/%Y'), self.hour_start.strftime('%H:%M'), self.get_total())
        return out

    def get_attendance_members(self):
        l = []
        for m in self.refer_agenda.members.all():
            l.append(dict(member=m, attendance=True if m in self.members.all() else False))
        return l

    def get_total(self):
        distance = 0
        for r in self.rounds.all():
            distance += r.get_total()
        return distance
