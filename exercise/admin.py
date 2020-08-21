from django.contrib import admin
from exercise.models import Stroke, EnergySystem, EnergySegment, Exercise
# Register your models here.


class StrokeAdmin(admin.ModelAdmin):
    pass

class EnergySystemAdmin(admin.ModelAdmin):
    pass

class EnergySegmentAdmin(admin.ModelAdmin):
    pass

class ExerciseAdmin(admin.ModelAdmin):
    pass

admin.site.register(Stroke, StrokeAdmin)
admin.site.register(EnergySystem, EnergySystemAdmin)
admin.site.register(EnergySegment, EnergySegmentAdmin)
admin.site.register(Exercise, ExerciseAdmin)
