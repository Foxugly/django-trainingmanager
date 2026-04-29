from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import Attendance, AttendanceStatus


@admin.register(AttendanceStatus)
class AttendanceStatusAdmin(TranslationAdmin):
    list_display = ["code", "label", "is_default", "order", "color", "is_active"]
    list_filter = ["is_active", "is_default"]
    search_fields = ["code", "label"]
    fields = ["code", "label", "is_default", "order", "color", "is_active"]


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ["event", "member", "status", "created_at", "updated_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["event__name", "member__firstname", "member__lastname"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["event", "member"]
