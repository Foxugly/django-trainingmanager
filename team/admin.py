from django.contrib import admin

from .models import Team, TeamJoinRequest


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'is_active', 'is_public', 'created_at')
    list_filter = ('is_active', 'is_public')
    search_fields = ('name',)
    filter_horizontal = ('managers',)


@admin.register(TeamJoinRequest)
class TeamJoinRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'status', 'requested_at', 'responded_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'team__name')
