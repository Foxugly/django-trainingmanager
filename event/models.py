from django.db import models
from django.utils.translation import gettext as _

from member.models import Member
from round.models import Round


class Event(models.Model):
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s %d" % (_("Event"), self.pk)
