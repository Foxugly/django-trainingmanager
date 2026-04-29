from django.contrib import admin

from program.models import Program


class ProgramAdmin(admin.ModelAdmin):
    filter_horizontal = ["events"]


admin.site.register(Program, ProgramAdmin)
