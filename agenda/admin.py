from django.contrib import admin
from agenda.models import Agenda
# Register your models here.


class AgendaAdmin(admin.ModelAdmin):
    filter_horizontal = ['events', 'members']


admin.site.register(Agenda, AgendaAdmin)
