from rest_framework import serializers

from event.models import Event
from member.models import Member

from .models import Agenda


class AgendaSerializer(serializers.ModelSerializer):
    events = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Event.objects.all(), required=False
    )
    members = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Member.objects.all(), required=False
    )

    class Meta:
        model = Agenda
        fields = ['id', 'name', 'date_start', 'date_end', 'team', 'events', 'members']
        read_only_fields = ['id']
