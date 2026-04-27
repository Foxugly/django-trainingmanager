from rest_framework import serializers

from .models import Team, TeamJoinRequest


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = [
            'id', 'name', 'owner', 'managers',
            'is_active', 'is_public',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']


class TeamJoinRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamJoinRequest
        fields = [
            'id', 'user', 'team', 'status', 'message',
            'response_message', 'requested_at', 'responded_at',
            'responded_by',
        ]
        read_only_fields = [
            'id', 'user', 'requested_at', 'responded_at', 'responded_by',
        ]


class CreateJoinRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamJoinRequest
        fields = ['id', 'team', 'message']
        read_only_fields = ['id']

    def validate(self, data):
        user = self.context['request'].user
        team = data['team']
        member_profile = getattr(user, 'member_profile', None)
        if member_profile is not None and member_profile.teams.filter(pk=team.pk).exists():
            raise serializers.ValidationError(
                {"team": "Vous etes deja membre de cette team."}
            )
        if TeamJoinRequest.objects.filter(user=user, team=team, status='pending').exists():
            raise serializers.ValidationError(
                {"team": "Vous avez deja une demande en attente pour cette team."}
            )
        if not team.is_active:
            raise serializers.ValidationError({"team": "Cette team est inactive."})
        if not team.is_public:
            raise serializers.ValidationError({"team": "Cette team n'est pas publique."})
        return data
