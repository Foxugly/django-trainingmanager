from rest_framework import viewsets

from tools.permissions import AdminWriteAuthRead

from .models import Sport
from .serializers import SportAdminSerializer, SportSerializer


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
