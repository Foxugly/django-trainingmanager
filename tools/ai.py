"""Low-level wrapper around the Anthropic Claude API.

Higher-level features (program generation, training generation, etc.)
should sit in domain-specific modules and call into this one.
"""

import logging
from typing import Optional

from anthropic import Anthropic, APIError, APITimeoutError, AuthenticationError

from django.conf import settings
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)


class AIServiceError(APIException):
    status_code = 502
    default_detail = "AI service unavailable. Please retry later."
    default_code = "ai_service_error"


class AIConfigurationError(APIException):
    status_code = 500
    default_detail = "AI service is not configured."
    default_code = "ai_configuration_error"


def _get_client() -> Anthropic:
    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        raise AIConfigurationError(
            "ANTHROPIC_API_KEY is not set. Configure it in .env."
        )
    return Anthropic(
        api_key=api_key,
        timeout=settings.ANTHROPIC_TIMEOUT_SECONDS,
    )


def call_claude(
    prompt: str,
    *,
    system: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> dict:
    """Send a single user prompt to Claude and return the response payload."""
    client = _get_client()

    kwargs = {
        "model": model or settings.ANTHROPIC_MODEL_DEFAULT,
        "max_tokens": max_tokens or settings.ANTHROPIC_MAX_TOKENS_DEFAULT,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system

    try:
        response = client.messages.create(**kwargs)
    except AuthenticationError as e:
        logger.error("Anthropic authentication failed: %s", e)
        raise AIConfigurationError("AI authentication failed. Check API key.")
    except APITimeoutError as e:
        logger.error("Anthropic API timeout: %s", e)
        raise AIServiceError("AI request timed out.")
    except APIError as e:
        logger.error("Anthropic API error: %s", e)
        raise AIServiceError(f"AI request failed: {e}")
    except Exception as e:
        logger.exception("Unexpected error calling Anthropic")
        raise AIServiceError(f"Unexpected error: {e}")

    text_content = ""
    for block in response.content:
        if hasattr(block, "text"):
            text_content += block.text

    return {
        "text": text_content,
        "model": response.model,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "stop_reason": response.stop_reason,
    }
