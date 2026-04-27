from rest_framework import serializers

from agenda.models import Agenda
from member.models import Member
from round.models import Round

from .models import Event


class EventSerializer(serializers.ModelSerializer):
    refer_agenda = serializers.PrimaryKeyRelatedField(
        queryset=Agenda.objects.all(), required=False, allow_null=True
    )
    rounds = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Round.objects.all(), required=False
    )
    members = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Member.objects.all(), required=False
    )

    class Meta:
        model = Event
        fields = [
            'id', 'name', 'goal', 'color',
            'date', 'hour_start', 'hour_end', 'total',
            'refer_agenda', 'rounds', 'members',
        ]
        read_only_fields = ['id']
