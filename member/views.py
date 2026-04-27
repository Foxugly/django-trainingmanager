from rest_framework import viewsets

from .models import Member
from .serializers import MemberSerializer


class MemberViewSet(viewsets.ModelViewSet):
    """CRUD complet pour Member."""
    queryset = Member.objects.all().order_by('lastname', 'firstname')
    serializer_class = MemberSerializer
