from rest_framework import serializers

from .models import CustomUser


class CustomUserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user payload for nested read contexts (owner, invited_by, etc.)."""

    class Meta:
        model = CustomUser
        fields = ["id", "username", "first_name", "last_name", "email"]
        read_only_fields = fields


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "language",
            "is_staff",
            "is_superuser",
            "last_login",
            "date_joined",
        ]
        read_only_fields = [
            "id",
            "username",
            "is_staff",
            "is_superuser",
            "last_login",
            "date_joined",
        ]
