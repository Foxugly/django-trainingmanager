from rest_framework import serializers

from .models import CustomUser


class CustomUserPublicSerializer(serializers.ModelSerializer):
    """Public user payload for nested read contexts.

    Excludes email and other privacy-sensitive fields. Use this whenever
    a user is exposed inside another resource (Team.owner, Member.user,
    TeamInvitation.invited_by, ...).
    """

    class Meta:
        model = CustomUser
        fields = ["id", "username", "first_name", "last_name"]
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
            "last_login",
            "date_joined",
        ]
        read_only_fields = [
            "id",
            "username",
            "last_login",
            "date_joined",
        ]
