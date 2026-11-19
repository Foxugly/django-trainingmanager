from django.db import models
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from member.models import Member
from round.models import Round
from tools.generic_class import GenericClass


# Create your models here.
class Event(GenericClass):
    name = models.CharField(max_length=100, verbose_name=_("name"))
    goal = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("goal"))
    color = models.CharField(max_length=10, blank=True, verbose_name=_("color"))
    date = models.DateField(blank=True, null=True, db_index=True)
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
        return self.members.count()

    def get_all_members(self):
        return self.refer_agenda.members.all()

    def get_nb_all_members(self):
        return self.refer_agenda.members.count()

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
        # prefetch exercises so each round's get_total()/get_row() doesn't re-hit
        # the DB (big win when rendering the event PDF).
        return self.rounds.all().order_by("order").prefetch_related("exercises")

    # The three builders below return SafeStrings made with format_html: rows
    # come from Round.get_row (escaped there) and every other value is escaped
    # here. Templates render them without |safe.
    def get_table(self):
        return format_html(
            "<table class='card-table table mb-0 table-bordered'>"
            "<thead><tr><th>#</th><th>Dist.</th><th>Round</th><th>Ex.</th><th></th></tr></thead><tbody>"
            "{}</tbody></table>",
            mark_safe("".join(r.get_row(True) for r in self.get_rounds())),
        )

    def get_table_raw(self):
        return format_html(
            "<table class='table mb-0'>"
            "<thead><tr><th>#</th><th>Dist.</th><th>Round</th><th>Exercices</th></tr></thead><tbody>"
            "{}</tbody></table>",
            mark_safe("".join(r.get_row(False) for r in self.get_rounds())),
        )

    def get_title_raw(self):
        return format_html(
            "<table class='table'>"
            "<thead><tr><th class='text-center' colspan=2>{}</th></tr></thead>"
            "<tbody><tr><td class='text-center'>Date : {}</td><td class='text-center'>Heure : {} </td></tr>"
            "<tr><td class='text-center' colspan=2>Distance : {} m</td></tr></tbody></table>",
            self.refer_agenda, self.date.strftime('%d/%m/%Y'), self.hour_start.strftime('%H:%M'), self.get_total(),
        )

    def get_attendance_members(self):
        # Resolve membership with one query (a set of present pks) instead of
        # re-evaluating self.members.all() inside the loop (N+1).
        present_ids = set(self.members.values_list("pk", flat=True))
        return [dict(member=m, attendance=m.pk in present_ids)
                for m in self.refer_agenda.members.all()]

    def get_total(self):
        distance = 0
        for r in self.rounds.all():
            distance += r.get_total()
        return distance
