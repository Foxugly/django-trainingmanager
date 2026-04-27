from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from .serializers import MeSerializer


class MeView(RetrieveUpdateAPIView):
    """GET/PATCH du profil de l'utilisateur connecté."""

    serializer_class = MeSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
