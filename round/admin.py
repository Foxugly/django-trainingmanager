from django.contrib import admin

from round.models import Round


# Register your models here.


class RoundAdmin(admin.ModelAdmin):
    filter_horizontal = ('exercises',)


admin.site.register(Round, RoundAdmin)
