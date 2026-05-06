from django.contrib import admin

from .models import Team, TeamInvitation, TeamJoinRequest, TeamMembership


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "is_active", "is_public", "created_at")
    list_filter = ("is_active", "is_public")
    search_fields = ("name",)
    filter_horizontal = ("managers", "attendance_statuses")


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


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ("team", "member", "joined_at", "left_at", "active")
    list_filter = ("team", "left_at")
    search_fields = ("team__name", "member__firstname", "member__lastname")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("team", "member")

    @admin.display(boolean=True, description="Active")
    def active(self, obj):
        return obj.left_at is None
