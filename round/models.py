from django.db import models
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from exercise.models import Exercise
from tools.generic_class import GenericClass


# Create your models here.
class Round(GenericClass):
    order = models.PositiveIntegerField(default=1, db_index=True)
    count = models.PositiveIntegerField(default=1)
    t_start = models.CharField(max_length=10, null=True, blank=True, verbose_name=_("start"), )
    t_break = models.CharField(max_length=10, null=True, blank=True, verbose_name=_("break"), )
    exercises = models.ManyToManyField(Exercise, blank=True, )
    refer_event = models.ForeignKey('event.Event', verbose_name=_('refer_event'), related_name='back_event', blank=True,
                                    null=True, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.refer_event:
            # M2M add() is idempotent (DB-level get_or_create) — no membership check needed.
            self.refer_event.rounds.add(self)

    def get_row(self, buttons):
        # Built with format_html: every value (t_break, t_start, the exercise
        # text with its free-form notes, stroke and segment names) is escaped.
        # It used to be %-interpolated raw and rendered with |safe — stored XSS
        # on the event page and HTML injection into the wkhtmltopdf export.
        exercises = sorted(self.exercises.all(), key=lambda ex: ex.order)
        nb = len(exercises)
        rows = []
        for i, e in enumerate(exercises):
            if i == 0:
                row = format_html(
                    '<tr>'
                    '<th class="text-center align-middle" rowspan="{}">#{}</th>'
                    '<td class="align-middle text-center" rowspan="{}">{}</td>'
                    '<td class="align-middle text-center" rowspan="{}">{} X {} {}</td>'
                    '<td>{}</td>',
                    nb, self.order, nb, self.get_total(), nb, self.count,
                    format_html("<BR>break : {}", self.t_break) if self.t_break else " ",
                    format_html("<BR>start : {}", self.t_start) if self.t_start else " ",
                    e.get_row(),
                )
                if buttons:
                    row += format_html(
                        '<td style="width:95px" class="align-middle text-center" rowspan="{}">'
                        '<button class="bs-modal btn btn-sm btn-info" type="button" data-form-url="{}" data-next="{}">'
                        '<span class="fa fa-edit"></span>'
                        '</button> '
                        '<button class="bs-modal btn btn-sm btn-danger" type="button" data-form-url="{}" data-next="{}">'
                        '<span class="fa fa-trash"></span>'
                        '</button>'
                        '</td>',
                        nb, self.get_change_url(), self.refer_event.get_absolute_url(), self.get_delete_url(),
                        self.refer_event.get_absolute_url(),
                    )
                rows.append(row + mark_safe('</tr>'))
            else:
                rows.append(format_html("<tr><td>{}</td></tr>", e.get_row()))
        return mark_safe("".join(rows))

    def get_total(self):
        distance = 0
        for e in self.exercises.all():
            distance += e.get_total()
        return self.count * distance

    def __str__(self):
        return "[#%d] %s %d" % (self.order, _('Round'), self.id)

    class Meta:
        verbose_name = _('Round')
