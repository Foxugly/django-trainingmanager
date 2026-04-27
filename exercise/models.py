from django.db import models
from django.utils.translation import gettext as _

from tools.generic_class import GenericClass


class Stroke(GenericClass):
    name = models.CharField(max_length=20, verbose_name=_("name"))

    def __str__(self):
        return self.name


class EnergySystem(GenericClass):
    name = models.CharField(max_length=20, verbose_name=_("name"))

    def __str__(self):
        return self.name


class EnergySegment(GenericClass):
    abv = models.CharField(max_length=10, verbose_name=_("abv"))
    description = models.CharField(max_length=200, null=True, blank=True, verbose_name=_("description"))
    energysystem = models.ForeignKey(EnergySystem, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return '%s (%s)' % (self.abv, self.energysystem)


class Exercise(GenericClass):
    order = models.IntegerField(verbose_name=_("order"), default=1)
    t_start = models.CharField(max_length=10, null=True, blank=True, verbose_name=_("start"), )
    t_break = models.CharField(max_length=10, null=True, blank=True, verbose_name=_("break"), )
    repetition = models.PositiveIntegerField(verbose_name=_("repetition"), default=1)
    distance = models.PositiveIntegerField(verbose_name=_("distance"), default=100)
    stroke = models.ForeignKey(Stroke, verbose_name=_("stroke"), null=True, blank=True, on_delete=models.CASCADE)
    energysegment = models.ForeignKey(EnergySegment, null=True, blank=True, verbose_name=_("Energy Segment"),
                                      on_delete=models.CASCADE)
    notes = models.CharField(max_length=200, blank=True, verbose_name=_("notes"), )

    def get_total(self):
        return self.repetition * self.distance

    def __str__(self):
        return "%s %d" % (_('Exercise'), self.id)

    class Meta:
        verbose_name = _('Exercise')
