import logging

from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers as drf_serializers
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Team, TeamJoinRequest
from .permissions import IsJoinRequestParticipant, IsTeamOwnerOrReadOnly
from .serializers import (
    CreateJoinRequestSerializer,
    TeamJoinRequestSerializer,
    TeamSerializer,
)

logger = logging.getLogger(__name__)


class TeamViewSet(viewsets.ModelViewSet):
    """CRUD sur Teams. Liste = teams gérées par l'user + teams publiques actives."""
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, IsTeamOwnerOrReadOnly]
    filterset_fields = ['is_active', 'is_public']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        user = self.request.user
        return Team.objects.filter(
            Q(owner=user)
            | Q(managers=user)
            | Q(is_public=True, is_active=True)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TeamJoinRequestViewSet(viewsets.ModelViewSet):
    """
    Self-signup join request flow.
    - POST   /join-requests/        : create (any authenticated user)
    - GET    /join-requests/        : own + managed teams' requests
    - GET    /join-requests/{id}/   : detail (participant only)
    - PATCH  /join-requests/{id}/   : cancel (requester) or accept/reject (manager)
    """
    permission_classes = [IsAuthenticated, IsJoinRequestParticipant]
    filterset_fields = ['status', 'team']
    ordering_fields = ['requested_at', 'responded_at']
    ordering = ['-requested_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateJoinRequestSerializer
        return TeamJoinRequestSerializer

    def get_queryset(self):
        user = self.request.user
        managed = Team.objects.filter(Q(owner=user) | Q(managers=user))
        return TeamJoinRequest.objects.filter(
            Q(user=user) | Q(team__in=managed)
        ).distinct()

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        self._notify_managers(instance)

    def _notify_managers(self, join_request):
        from django.conf import settings as dj_settings
        from django.core.mail import send_mail

        team = join_request.team
        recipients = list(team.managers.values_list('email', flat=True))
        if team.owner.email:
            recipients.append(team.owner.email)
        recipients = [r for r in recipients if r]

        if not recipients:
            return

        subject = f"[TrainingManager] Nouvelle demande de {join_request.user.username}"
        body = (
            f"L'utilisateur {join_request.user.username} ({join_request.user.email}) "
            f"souhaite rejoindre votre team \"{team.name}\".\n\n"
            f"Message : {join_request.message or '(aucun)'}\n\n"
            f"Connectez-vous pour repondre."
        )
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=dj_settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False,
            )
        except Exception:
            logger.exception("Failed to send join request notification email")

    def perform_update(self, serializer):
        instance = serializer.instance
        new_status = serializer.validated_data.get('status', instance.status)

        if new_status == instance.status:
            serializer.save()
            return

        if instance.status != 'pending':
            raise drf_serializers.ValidationError(
                {"status": "Cette demande a deja ete traitee."}
            )

        if new_status == 'cancelled':
            if instance.user_id != self.request.user.pk:
                raise drf_serializers.ValidationError(
                    {"status": "Seul l'auteur de la demande peut l'annuler."}
                )
            serializer.save(responded_at=timezone.now())
            return

        if new_status in ('accepted', 'rejected'):
            if not instance.team.is_managed_by(self.request.user):
                raise drf_serializers.ValidationError(
                    {"status": "Seul un manager peut accepter ou refuser."}
                )
            saved = serializer.save(
                responded_at=timezone.now(),
                responded_by=self.request.user,
            )
            if new_status == 'accepted':
                self._handle_acceptance(saved)
            return

        raise drf_serializers.ValidationError(
            {"status": f"Transition non autorisee vers {new_status}."}
        )

    def _handle_acceptance(self, join_request):
        from member.models import Member

        user = join_request.user
        team = join_request.team

        existing_member = getattr(user, 'member_profile', None)
        if existing_member is not None:
            existing_member.teams.add(team)
            return

        member = Member.objects.create(
            firstname=user.first_name or user.username,
            lastname=user.last_name or '',
            email=user.email,
            phonenumber='',
            user=user,
        )
        member.teams.add(team)
