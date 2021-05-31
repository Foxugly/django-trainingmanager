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
    refer_round = models.ForeignKey('round.Round', verbose_name=_('refer_round'), related_name='back_round', blank=True,
                                    null=True, on_delete=models.CASCADE)

    def get_total(self):
        return self.repetition * self.distance

    def get_row(self):
        
        out = "[%s]" % self.energysegment if self.energysegment else ""
        if self.repetition > 1:
            out += " %d x" % self.repetition if self.repetition > 0 else ""
        out += " %d m :" % self.distance if self.distance > 0 else ""
        out += " %s %s" % (self.stroke, self.notes)
        if self.t_break:
            out += " break : %s" % self.t_break
        if self.t_start:
            out += " start : %s" % self.t_start

        return out

    def __str__(self):
        return "%s %d" % (_('Exercise'), self.id)

    class Meta:
        verbose_name = _('Exercise')
