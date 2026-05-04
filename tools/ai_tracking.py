"""Tracking helper for Anthropic API consumption.

Each successful Anthropic call is recorded as an AIUsage row scoped to
a Team and a User (both nullable, e.g. for /ai/ping/ which has no team
context, or admin / scripted calls).

Tracking failures are logged but never raised — a tracking error must
not break the user-facing API call.
"""

import logging

logger = logging.getLogger(__name__)


def track_ai_usage(response, *, team=None, user=None, endpoint, model_used):
    """Record an Anthropic API call.

    Args:
        response: Anthropic SDK response object (must expose `.usage`).
        team: Team instance or None.
        user: User instance or None.
        endpoint: AIUsage.Endpoint value ('ping' | 'plan' | 'training').
        model_used: Anthropic model identifier (e.g. 'claude-haiku-4-5').

    Returns:
        AIUsage instance on success, or None on tracking failure.
    """
    try:
        from aiusage.models import AIUsage

        usage = getattr(response, "usage", None)
        return AIUsage.objects.create(
            team=team,
            user=user,
            endpoint=endpoint,
            model_used=model_used,
            input_tokens=int(getattr(usage, "input_tokens", 0) or 0),
            output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
            cache_creation_tokens=int(getattr(usage, "cache_creation_input_tokens", 0) or 0),
            cache_read_tokens=int(getattr(usage, "cache_read_input_tokens", 0) or 0),
        )
    except Exception:
        # I8: billing failure is a monetisation blocker, not a warning.
        # An AIUsage row that never gets recorded means the tokens were
        # consumed (and paid for) without an audit trail or cost cap
        # signal. Surface as ERROR so monitoring (and any future Sentry
        # / alerting) treats it as actionable.
        logger.error("Failed to track AI usage", exc_info=True)
        return None
