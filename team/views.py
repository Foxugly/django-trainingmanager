import logging

from django.conf import settings as dj_settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers as drf_serializers
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Team, TeamInvitation, TeamJoinRequest
from .permissions import (
    IsJoinRequestParticipant,
    IsTeamOwnerOrReadOnly,
    IsTrainer,
)
from .serializers import (
    CompleteInvitationSerializer,
    CreateInvitationSerializer,
    CreateJoinRequestSerializer,
    TeamInvitationSerializer,
    TeamJoinRequestSerializer,
    TeamSerializer,
    ValidateInvitationSerializer,
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
    """Self-signup join request flow."""
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


class TeamInvitationViewSet(viewsets.ModelViewSet):
    """Trainer invitation flow."""
    permission_classes = [IsAuthenticated, IsTrainer]
    filterset_fields = ['status', 'team']
    ordering_fields = ['created_at', 'expires_at']
    ordering = ['-created_at']
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateInvitationSerializer
        return TeamInvitationSerializer

    def get_queryset(self):
        user = self.request.user
        managed = Team.objects.filter(Q(owner=user) | Q(managers=user))
        return TeamInvitation.objects.filter(team__in=managed).distinct()

    @extend_schema(
        request=CreateInvitationSerializer,
        responses={
            201: TeamInvitationSerializer,
        },
        description=(
            'Trainer pre-registers an athlete on a managed team. '
            'If the email matches an existing user, the response payload '
            'is {detail, member_id} instead of a TeamInvitation.'
        ),
    )
    def create(self, request, *args, **kwargs):
        from member.models import Member

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        User = get_user_model()
        existing_user = User.objects.filter(email=data['email']).first()

        member = Member.objects.create(
            firstname=data['firstname'],
            lastname=data['lastname'],
            email=data['email'],
            phonenumber=data.get('phonenumber', ''),
            user=existing_user,
        )
        member.teams.add(data['team'])

        if existing_user is not None:
            self._send_existing_user_notification(existing_user, data['team'])
            return Response(
                {
                    "detail": "User already exists; Member created and linked.",
                    "member_id": member.id,
                },
                status=status.HTTP_201_CREATED,
            )

        invitation = TeamInvitation.objects.create(
            team=data['team'],
            invited_by=request.user,
            member=member,
            email=data['email'],
        )
        self._send_invitation_email(invitation)
        return Response(
            TeamInvitationSerializer(invitation, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    def _send_invitation_email(self, invitation):
        frontend_url = dj_settings.FRONTEND_URL.rstrip('/')
        link = f"{frontend_url}/invitation/{invitation.token}"
        subject = f"[TrainingManager] Vous etes invite dans {invitation.team.name}"
        body = (
            f"Bonjour {invitation.member.firstname},\n\n"
            f"{invitation.invited_by.username} vous a invite a rejoindre "
            f"la team \"{invitation.team.name}\".\n\n"
            f"Pour finaliser votre inscription, cliquez sur ce lien :\n"
            f"{link}\n\n"
            f"Le lien est valable jusqu'au {invitation.expires_at.strftime('%d/%m/%Y')}.\n"
        )
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=dj_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[invitation.email],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Failed to send invitation email")

    def _send_existing_user_notification(self, user, team):
        subject = f"[TrainingManager] Vous avez ete ajoute a {team.name}"
        body = (
            f"Bonjour {user.first_name or user.username},\n\n"
            f"Vous avez ete ajoute a la team \"{team.name}\". "
            f"Vous pouvez vous y connecter depuis votre compte existant.\n"
        )
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=dj_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Failed to send existing-user notification")

    def perform_destroy(self, instance):
        if instance.status != 'pending':
            raise drf_serializers.ValidationError(
                {"detail": "Seules les invitations pending peuvent etre annulees."}
            )
        instance.status = 'cancelled'
        instance.save()


class InvitationLookupView(APIView):
    """Public endpoint to validate and finalize an invitation token."""
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        responses={
            200: ValidateInvitationSerializer,
            400: OpenApiResponse(description='Invitation not pending (already handled)'),
            404: OpenApiResponse(description='Token not found'),
            410: OpenApiResponse(description='Invitation expired'),
        },
        description='Lookup an invitation by token. No authentication required.',
    )
    def get(self, request, token):
        invitation = get_object_or_404(TeamInvitation, token=token)
        if not invitation.is_valid():
            if invitation.status == 'pending' and timezone.now() > invitation.expires_at:
                invitation.status = 'expired'
                invitation.save()
                return Response(
                    {"detail": "Invitation expired."},
                    status=status.HTTP_410_GONE,
                )
            return Response(
                {"detail": f"Invitation {invitation.status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(ValidateInvitationSerializer(invitation).data)

    @extend_schema(
        request=CompleteInvitationSerializer,
        responses={
            201: OpenApiResponse(
                response=inline_serializer(
                    name='CompleteInvitationResponse',
                    fields={
                        'detail': drf_serializers.CharField(),
                        'username': drf_serializers.CharField(),
                        'access': drf_serializers.CharField(),
                        'refresh': drf_serializers.CharField(),
                    },
                ),
                description='User created and JWT issued',
            ),
            400: OpenApiResponse(description='Invalid token state, username taken, or weak password'),
            404: OpenApiResponse(description='Token not found'),
        },
        description='Finalize invitation: create the user, link Member, return JWT.',
    )
    def post(self, request, token):
        from allauth.account.models import EmailAddress
        from rest_framework_simplejwt.tokens import RefreshToken

        invitation = get_object_or_404(TeamInvitation, token=token)
        if not invitation.is_valid():
            return Response(
                {"detail": f"Invitation {invitation.status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CompleteInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        User = get_user_model()
        user = User.objects.create_user(
            username=serializer.validated_data['username'],
            email=invitation.email,
            password=serializer.validated_data['password'],
        )
        user.first_name = invitation.member.firstname
        user.last_name = invitation.member.lastname
        user.is_active = True
        user.save()
        EmailAddress.objects.create(
            user=user,
            email=invitation.email,
            verified=True,
            primary=True,
        )
        invitation.member.user = user
        invitation.member.save()

        invitation.status = 'completed'
        invitation.completed_at = timezone.now()
        invitation.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "detail": "Compte cree et invitation finalisee.",
                "username": user.username,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )
