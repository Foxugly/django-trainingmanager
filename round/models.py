from django.db import models
from django.utils.translation import gettext as _

from exercise.models import Exercise
from tools.generic_class import GenericClass


class Round(GenericClass):
    order = models.PositiveIntegerField(default=1)
    count = models.PositiveIntegerField(default=1)
    t_start = models.CharField(max_length=10, null=True, blank=True, verbose_name=_("start"), )
    t_break = models.CharField(max_length=10, null=True, blank=True, verbose_name=_("break"), )
    exercises = models.ManyToManyField(Exercise, blank=True, )

    def get_total(self):
        distance = 0
        for e in self.exercises.all():
            distance += e.get_total()
        return self.count * distance

    def __str__(self):
        return "%s %d" % (_('Round'), self.id)

    class Meta:
        verbose_name = _('Round')
