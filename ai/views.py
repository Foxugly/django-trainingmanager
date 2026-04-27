from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from team.permissions import IsTrainer
from tools.ai import call_claude
from tools.throttling import AIPingThrottle


class AIPingView(APIView):
    """POST /api/v1/ai/ping/ — minimal Claude call for diagnostics."""
    permission_classes = [IsAuthenticated, IsTrainer]
    throttle_classes = [AIPingThrottle]

    @extend_schema(
        request=inline_serializer(
            name='AIPingRequest',
            fields={
                'prompt': serializers.CharField(
                    required=False,
                    help_text="Prompt to send to Claude. Defaults to a hello-world prompt.",
                ),
            },
        ),
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='AIPingResponse',
                    fields={
                        'text': serializers.CharField(),
                        'model': serializers.CharField(),
                        'input_tokens': serializers.IntegerField(),
                        'output_tokens': serializers.IntegerField(),
                        'stop_reason': serializers.CharField(),
                    },
                ),
                description='Claude responded successfully',
            ),
            400: OpenApiResponse(description='Invalid prompt'),
            500: OpenApiResponse(description='AI configuration error'),
            502: OpenApiResponse(description='AI service error'),
        },
        description='Diagnostic ping to the Anthropic API.',
    )
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
