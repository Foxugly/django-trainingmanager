from django.contrib import admin

from .models import Team


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'is_active', 'is_public', 'created_at')
    list_filter = ('is_active', 'is_public')
    search_fields = ('name',)
    filter_horizontal = ('managers',)
