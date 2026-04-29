from django.contrib import admin

from .models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ["created_at", "team", "member", "author", "is_active"]
    list_filter = ["is_active", "team", "created_at"]
    search_fields = [
        "member__firstname",
        "member__lastname",
        "author__username",
    ]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["team", "member", "author"]
