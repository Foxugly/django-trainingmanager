from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from tools.openapi import INCLUDE_INACTIVE_PARAM
from tools.permissions import AdminWriteAuthRead

from .models import Sport
from .serializers import SportAdminSerializer, SportSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List sports (public flavor)",
        description=(
            "Returns the public Sport serializer with localized 'name'. "
            "Available to all authenticated users."
        ),
        responses=SportSerializer,
        parameters=[INCLUDE_INACTIVE_PARAM],
    ),
    retrieve=extend_schema(
        summary="Retrieve sport (admin flavor for staff)",
        description=(
            "Returns the admin flavor with name_fr/nl/en/it/es when called "
            "by a staff user, otherwise the public flavor."
        ),
        responses=SportAdminSerializer,
        parameters=[INCLUDE_INACTIVE_PARAM],
    ),
    create=extend_schema(
        summary="Create sport (staff only)",
        description="Accepts the admin flavor with name_fr/nl/en/it/es.",
        request=SportAdminSerializer,
        responses=SportAdminSerializer,
    ),
    update=extend_schema(
        request=SportAdminSerializer,
        responses=SportAdminSerializer,
        parameters=[INCLUDE_INACTIVE_PARAM],
    ),
    partial_update=extend_schema(
        request=SportAdminSerializer,
        responses=SportAdminSerializer,
        parameters=[INCLUDE_INACTIVE_PARAM],
    ),
    destroy=extend_schema(
        summary="Soft delete sport (staff only)",
        description="Sets is_active=False; does not hard delete.",
    ),
)
class SportViewSet(viewsets.ModelViewSet):
    """CRUD on the Sport referential.

    Read: any authenticated user (default queryset filters is_active=True).
    Write: staff only. Soft delete via perform_destroy.
    Staff can pass ?include_inactive=true to see inactive entries.
    """

    permission_classes = [AdminWriteAuthRead]
    filterset_fields = ["is_active"]
    search_fields = ["name", "slug"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Sport.objects.none()

        qs = Sport.objects.all().prefetch_related("energy_systems")
        include_inactive = self.request.query_params.get("include_inactive") == "true"
        if not (include_inactive and self.request.user.is_staff):
            qs = qs.filter(is_active=True)
        return qs

    def get_serializer_class(self):
        if (
            self.request.user.is_authenticated
            and self.request.user.is_staff
            and self.action in ("create", "update", "partial_update", "retrieve")
        ):
            return SportAdminSerializer
        return SportSerializer

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])
