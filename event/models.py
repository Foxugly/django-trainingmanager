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
    date = models.DateField(
        blank=True,
        null=True,
    )
    hour_start = models.TimeField(
        blank=True,
        null=True,
    )
    hour_end = models.TimeField(
        blank=True,
        null=True,
    )
    total = models.PositiveIntegerField(default=0)
    rounds = models.ManyToManyField(
        Round,
        blank=True,
    )
    members = models.ManyToManyField(
        Member,
        blank=True,
    )
    refer_program = models.ForeignKey(
        "program.Program",
        verbose_name=_("refer_program"),
        related_name="back_program",
        null=True,
        on_delete=models.CASCADE,
    )
    generated_by_ai = models.BooleanField(default=False)
    ai_prompt = models.TextField(blank=True, default="")
    ai_response = models.TextField(blank=True, default="")
    ai_generated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "%s %d" % (_("Event"), self.pk)

    def get_members_present(self):
        return self.members.all()

    def get_nb_members_present(self):
        return len(self.get_members_present())

    def get_all_members(self):
        return self.refer_program.members.all()

    def get_nb_all_members(self):
        return len(self.get_all_members())

    @staticmethod
    def hour_t(t):
        return t.strftime("%H:%M:%S")

    def start_t(self):
        return self.date.strftime("%Y-%m-%d") + "T" + self.hour_t(self.hour_start)

    def end_t(self):
        return self.date.strftime("%Y-%m-%d") + "T" + self.hour_t(self.hour_end)

    def as_json(self):
        return dict(
            id=str(self.id),
            start=self.start_t(),
            end=self.end_t(),
            title=self.name,
            color=self.color,
        )

    def get_attendance_members(self):
        l = []
        for m in self.refer_program.members.all():
            l.append(dict(member=m, attendance=True if m in self.members.all() else False))
        return l

    def get_total(self):
        distance = 0
        for r in self.rounds.all():
            distance += r.get_total()
        return distance
