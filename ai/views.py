from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from team.permissions import IsTrainer
from tools.ai import call_claude


class AIPingView(APIView):
    """POST /api/v1/ai/ping/ — minimal Claude call for diagnostics."""
    permission_classes = [IsAuthenticated, IsTrainer]

    def post(self, request):
        prompt = request.data.get("prompt", "Say hello in one word.")
        if not isinstance(prompt, str) or not prompt.strip():
            return Response(
                {"detail": "prompt must be a non-empty string"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(prompt) > 5000:
            return Response(
                {"detail": "prompt too long (max 5000 chars for ping)"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = call_claude(prompt)
        return Response(result, status=status.HTTP_200_OK)
