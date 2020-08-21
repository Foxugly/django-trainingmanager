from django.contrib import admin
from event.models import Event
# Register your models here.


class EventAdmin(admin.ModelAdmin):
    filter_horizontal = ['rounds', 'members']
    pass


admin.site.register(Event, EventAdmin)
