from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from .serializers import MeSerializer


class MeView(RetrieveUpdateAPIView):
    """GET/PATCH du profil de l'utilisateur connecté.

    PUT is intentionally disabled to prevent partial bodies from resetting
    unspecified writable fields (first_name, last_name, language) to their
    defaults. Use PATCH for any update.

    `email` is read-only here; changing the email requires admin intervention
    in v1 (a verified change-email flow is deferred to v2).
    """

    serializer_class = MeSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user
