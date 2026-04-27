from django.contrib import admin

from .models import Team, TeamInvitation, TeamJoinRequest


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "is_active", "is_public", "created_at")
    list_filter = ("is_active", "is_public")
    search_fields = ("name",)
    filter_horizontal = ("managers",)


@admin.register(TeamJoinRequest)
class TeamJoinRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "team", "status", "requested_at", "responded_at")
    list_filter = ("status",)
    search_fields = ("user__username", "team__name")


@admin.register(TeamInvitation)
class TeamInvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "team", "status", "invited_by", "created_at", "expires_at")
    list_filter = ("status", "team")
    search_fields = ("email",)
    readonly_fields = ("token", "created_at", "completed_at")
