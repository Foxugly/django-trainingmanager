from rest_framework import viewsets

from .models import Round
from .serializers import RoundSerializer


class RoundViewSet(viewsets.ModelViewSet):
    """CRUD complet pour Round."""
    queryset = Round.objects.all().order_by('refer_event', 'order')
    serializer_class = RoundSerializer
