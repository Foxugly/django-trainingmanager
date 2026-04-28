from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import SAFE_METHODS, BasePermission


class AdminWriteAuthRead(BasePermission):
    """Read for any authenticated user; write for staff only.

    Used on the catalog referential viewsets (Sport, Modality,
    EnergySystem, EnergySegment) where any authenticated user must
    be able to read but only staff can mutate.
    """

    message = _("Only staff users can modify the catalog referential.")

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user.is_staff)
