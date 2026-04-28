from modeltranslation.translator import TranslationOptions, register

from .models import EnergySegment, EnergySystem, Modality


@register(Modality)
class ModalityTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(EnergySystem)
class EnergySystemTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(EnergySegment)
class EnergySegmentTranslationOptions(TranslationOptions):
    # 'abv' kept untranslated — it is a short technical code (Z0..Z7)
    fields = ("description",)
