from modeltranslation.translator import TranslationOptions, register

from .models import Sport


@register(Sport)
class SportTranslationOptions(TranslationOptions):
    fields = ("name",)
