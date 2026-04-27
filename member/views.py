from rest_framework import viewsets

from .models import Member
from .serializers import MemberSerializer


class MemberViewSet(viewsets.ModelViewSet):
    """CRUD complet pour Member."""
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    filterset_fields = ['lastname', 'firstname']
    search_fields = ['firstname', 'lastname', 'email']
    ordering_fields = ['lastname', 'firstname', 'id']
    ordering = ['lastname', 'firstname']
