"""AI-driven training plan generation for Program."""

import logging
from datetime import date as _date

from tools.ai import AIServiceError, call_claude_with_tool

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
        f"Tu es un coach expert en planification d'entrainement de {sport_name}. "
        f"Tu generes des plans d'entrainement structures et progressifs. "
        f"Tu adaptes la frequence, l'intensite et la variete en fonction des objectifs. "
        f"Tu DOIS toujours repondre en utilisant le tool 'create_training_plan'. "
        f"N'ecris jamais de texte libre."
    )


def build_user_prompt(*, sport_name, date_start, date_end, frequency_per_week, description):
    duration_days = (date_end - date_start).days + 1
    weeks = max(duration_days // 7, 1)
    expected_events = weeks * frequency_per_week

    return (
        f"Genere un plan d'entrainement avec ces contraintes :\n"
        f"- Sport : {sport_name}\n"
        f"- Periode : du {date_start.isoformat()} au {date_end.isoformat()} "
        f"({duration_days} jours, soit ~{weeks} semaines)\n"
        f"- Frequence : {frequency_per_week} seances par semaine "
        f"(soit ~{expected_events} seances au total)\n"
        f"- Objectifs et contraintes : {description or '(aucun precise)'}\n\n"
        f"Genere environ {expected_events} seances reparties intelligemment "
        f"sur la periode. Chaque seance doit avoir une date dans la range. "
        f"Varie les types d'effort (endurance, technique, intensite, recuperation) "
        f"selon une progression coherente."
    )


def _parse_date_strict(s):
    try:
        return _date.fromisoformat(s)
    except (TypeError, ValueError):
        raise AIServiceError(f"AI returned invalid date format: {s}")


def generate_plan(*, program, date_start, date_end, frequency_per_week, description):
    sport_name = program.team.sport.name if program.team.sport else "le sport pratique"

    system = build_system_prompt(sport_name)
    user_prompt = build_user_prompt(
        sport_name=sport_name,
        date_start=date_start,
        date_end=date_end,
        frequency_per_week=frequency_per_week,
        description=description,
    )

    result = call_claude_with_tool(
        prompt=user_prompt,
        system=system,
        tool=PLAN_TOOL_SCHEMA,
    )

    tool_input = result["tool_input"]
    events = tool_input.get("events", [])
    rationale = tool_input.get("rationale", "")

    if not isinstance(events, list) or not events:
        raise AIServiceError("AI returned an empty or invalid event list.")

    for ev in events:
        ev_date = _parse_date_strict(ev.get("date"))
        if ev_date < date_start or ev_date > date_end:
            raise AIServiceError(f"AI generated event with out-of-range date: {ev.get('date')}")

    return {
        "events": events,
        "rationale": rationale,
        "prompt_sent": user_prompt,
        "model": result["model"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
    }
