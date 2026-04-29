import re

from django.contrib import admin

from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        "created_at",
        "team",
        "author",
        "short_content",
        "edited_at",
        "deleted_at",
    ]
    list_filter = ["team", "created_at", "edited_at", "deleted_at"]
    search_fields = ["content", "author__username", "team__name"]
    readonly_fields = ["created_at", "edited_at"]
    raw_id_fields = ["team", "author"]

    @admin.display(description="Content (preview)")
    def short_content(self, obj):
        text = re.sub(r"<[^>]+>", "", obj.content or "")
        return text[:80] + ("..." if len(text) > 80 else "")
