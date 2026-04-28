"""AI-driven training plan generation for Program."""

import logging
from datetime import date as _date

from django.utils.translation import gettext_lazy as _

from tools.ai import AIServiceError, call_claude_with_tool
from tools.i18n import resolve_language_label

logger = logging.getLogger(__name__)


ALLOWED_COLORS = [
    "#3498db",  # blue
    "#2ecc71",  # green
    "#e74c3c",  # red
    "#f39c12",  # orange
    "#9b59b6",  # purple
    "#1abc9c",  # turquoise
]


PLAN_TOOL_SCHEMA = {
    "name": "create_training_plan",
    "description": (
        "Generate a training plan as a list of high-level Events (one per "
        "planned session). Each Event has a short name, a goal, a date, an "
        "approximate total distance, and a color from the allowed palette."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "maxLength": 100,
                            "description": "Short, descriptive session name",
                        },
                        "goal": {
                            "type": "string",
                            "maxLength": 100,
                            "description": "Main goal of the session",
                        },
                        "date": {
                            "type": "string",
                            "format": "date",
                            "description": "Date in YYYY-MM-DD format",
                        },
                        "total_distance": {
                            "type": "integer",
                            "minimum": 0,
                            "description": "Approximate total distance (meters)",
                        },
                        "color": {
                            "type": "string",
                            "enum": ALLOWED_COLORS,
                            "description": "Color from the allowed palette",
                        },
                    },
                    "required": ["name", "goal", "date", "total_distance", "color"],
                },
            },
            "rationale": {
                "type": "string",
                "description": "Overall plan explanation (3-5 sentences)",
            },
        },
        "required": ["events", "rationale"],
    },
}


def build_system_prompt(sport_name):
    return (
        f"You are an expert coach in {sport_name} training planning. "
        f"You generate structured and progressive training plans for athletes. "
        f"You adapt frequency, intensity, and variety based on the goals. "
        f"You MUST always respond using the 'create_training_plan' tool. "
        f"Never write free-form text."
    )


def build_user_prompt(
    *, sport_name, language, date_start, date_end, frequency_per_week, description
):
    duration_days = (date_end - date_start).days + 1
    weeks = max(duration_days // 7, 1)
    expected_events = weeks * frequency_per_week
    language_label = resolve_language_label(language)

    return (
        f"Generate a training plan with these constraints:\n"
        f"- Sport: {sport_name}\n"
        f"- Period: from {date_start.isoformat()} to {date_end.isoformat()} "
        f"({duration_days} days, ~{weeks} weeks)\n"
        f"- Frequency: {frequency_per_week} sessions per week "
        f"(~{expected_events} sessions total)\n"
        f"- Description and constraints provided by the coach: "
        f"{description or '(none)'}\n"
        f"\n"
        f"IMPORTANT instructions:\n"
        f"- The 'Description and constraints' above is provided by the coach "
        f"in {language_label}. It may contain critical information about the "
        f"athletes' age category, current performance level, training goals, "
        f"available equipment, or other constraints. Take ALL of this "
        f"information into account when designing the plan.\n"
        f"- Generate approximately {expected_events} sessions distributed "
        f"intelligently across the period. Each session must have a date "
        f"within the requested range.\n"
        f"- Vary effort types (endurance, technique, intensity, recovery) "
        f"following a coherent progression.\n"
        f"- Respond ENTIRELY in {language_label}: all event names, goals, "
        f"and the rationale must be in {language_label}.\n"
        f"- Use the 'create_training_plan' tool only.\n"
    )


def _parse_date_strict(s):
    try:
        return _date.fromisoformat(s)
    except (TypeError, ValueError):
        raise AIServiceError(_("AI returned an invalid date format."))


def generate_plan(*, program, date_start, date_end, frequency_per_week, description, user=None):
    sport_name = program.team.sport.name if program.team.sport else "the practiced sport"
    language = program.team.language

    system = build_system_prompt(sport_name)
    user_prompt = build_user_prompt(
        sport_name=sport_name,
        language=language,
        date_start=date_start,
        date_end=date_end,
        frequency_per_week=frequency_per_week,
        description=description,
    )

    result = call_claude_with_tool(
        prompt=user_prompt,
        system=system,
        tool=PLAN_TOOL_SCHEMA,
        track_kwargs={
            "team": program.team,
            "user": user,
            "endpoint": "plan",
        },
    )

    tool_input = result["tool_input"]
    events = tool_input.get("events", [])
    rationale = tool_input.get("rationale", "")

    if not isinstance(events, list) or not events:
        raise AIServiceError(_("AI returned an empty or invalid event list."))

    for ev in events:
        ev_date = _parse_date_strict(ev.get("date"))
        if ev_date < date_start or ev_date > date_end:
            raise AIServiceError(_("AI generated an event with an out-of-range date."))

    return {
        "events": events,
        "rationale": rationale,
        "prompt_sent": user_prompt,
        "model": result["model"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
    }
