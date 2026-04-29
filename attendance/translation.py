from modeltranslation.translator import TranslationOptions, register

from .models import AttendanceStatus


@register(AttendanceStatus)
class AttendanceStatusTranslationOptions(TranslationOptions):
    fields = ("label",)
