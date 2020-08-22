from django.db import models
from django.utils.translation import gettext as _

from exercise.models import Exercise
from tools.generic_class import GenericClass


# Create your models here.
class Round(GenericClass):
    order = models.PositiveIntegerField(default=0)
    count = models.PositiveIntegerField(default=0)
    t_start = models.CharField(max_length=10, null=True, blank=True, verbose_name=_("start"), )
    t_break = models.CharField(max_length=10, null=True, blank=True, verbose_name=_("break"), )
    exercises = models.ManyToManyField(Exercise, blank=True, )
    refer_event = models.ForeignKey('event.Event', verbose_name=_('refer_event'), related_name='back_event', blank=True,
                                    null=True, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        super(Round, self).save(*args, **kwargs)
        if self.refer_event:
            self.refer_event.rounds.add(self) if self not in self.refer_event.rounds.all() else None

    def get_row(self, buttons):
        out = ""
        nb = len(self.exercises.all())
        for i, e in enumerate(self.exercises.all().order_by('order')):
            if i == 0:
                out += '<tr>' \
                       '<th class="text-center align-middle" rowspan="%d">#%d</th>' \
                       '<td class="align-middle text-center" rowspan="%d">%d</td>' \
                       '<td class="align-middle text-center" rowspan="%d">%d X</td>' \
                       '<td>%s</td>' % (nb, self.order, nb, self.get_total(), nb, self.count, e.get_row())
                if buttons:
                    out += '<td style="width:95px" class="align-middle text-center" rowspan="%d">' \
                           '<button class="bs-modal btn btn-sm btn-info" type="button" data-form-url="%s" data-next="%s">' \
                           '<span class="fa fa-edit"></span>' \
                           '</button> ' \
                           '<button class="bs-modal btn btn-sm btn-danger" type="button" data-form-url="%s" data-next="%s">' \
                           '<span class="fa fa-trash"></span>' \
                           '</button>' \
                           '</td>' % (
                           nb, self.get_change_url(), self.refer_event.get_absolute_url(), self.get_delete_url(),
                           self.refer_event.get_absolute_url())
                out += '</tr>'
            else:
                out += "<tr><td>%s</td></tr>" % (e.get_row())
        return out

    def get_total(self):
        distance = 0
        for e in self.exercises.all():
            distance += e.get_total()
        return self.count * distance

    def __str__(self):
        return "%s %d" % (_('Round'), self.id)

    class Meta:
        verbose_name = _('Round')
