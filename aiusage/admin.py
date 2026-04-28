from django.contrib import admin

from .models import AIUsage


@admin.register(AIUsage)
class AIUsageAdmin(admin.ModelAdmin):
    list_display = [
        "created_at",
        "endpoint",
        "team",
        "user",
        "total_tokens",
        "model_used",
    ]
    list_filter = ["endpoint", "model_used", "created_at"]
    search_fields = ["team__name", "user__username"]
    readonly_fields = [f.name for f in AIUsage._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
