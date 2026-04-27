from rest_framework import serializers

from .models import CustomUser


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'language', 'is_foo_admin', 'is_staff', 'is_superuser',
            'last_login', 'date_joined',
        ]
        read_only_fields = [
            'id', 'username', 'is_foo_admin', 'is_staff', 'is_superuser',
            'last_login', 'date_joined',
        ]
