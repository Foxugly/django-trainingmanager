from django.contrib import admin

from exercise.models import EnergySegment, EnergySystem, Exercise, Modality


@admin.register(Modality)
class ModalityAdmin(admin.ModelAdmin):
    list_display = ("name", "sport")
    list_filter = ("sport",)
    search_fields = ("name",)


admin.site.register(EnergySystem)
admin.site.register(EnergySegment)
admin.site.register(Exercise)
