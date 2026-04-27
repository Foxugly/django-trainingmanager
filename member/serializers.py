from rest_framework import serializers

from .models import Member


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ['id', 'firstname', 'lastname', 'email', 'phonenumber']
        read_only_fields = ['id']
