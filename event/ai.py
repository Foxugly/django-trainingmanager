"""AI-driven training session generation for an Event."""

import logging

from django.utils.translation import gettext_lazy as _

from tools.ai import AIServiceError, call_claude_with_tool
from tools.i18n import resolve_language_label

logger = logging.getLogger(__name__)


def build_training_tool_schema(*, modality_ids, energysegment_ids):
    """Tool schema with the catalog ids fixed via enum to prevent hallucination."""
    return {
        "name": "create_training_session",
        "description": (
            "Generate the detail of a training session: a list of rounds, "
            "each containing exercises drawn from the provided catalog."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "rounds": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {
                            "count": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "How many times the round is repeated as a whole",
                            },
                            "t_start": {
                                "type": "string",
                                "pattern": "^[0-9]{2}:[0-9]{2}$",
                                "description": "MM:SS, '00:00' if not applicable",
                            },
                            "t_break": {
                                "type": "string",
                                "pattern": "^[0-9]{2}:[0-9]{2}$",
                                "description": "Pause after the round (MM:SS)",
                            },
                            "exercises": {
                                "type": "array",
                                "minItems": 1,
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "modality_id": {
                                            "type": "integer",
                                            "enum": modality_ids,
                                        },
                                        "energysegment_id": {
                                            "type": "integer",
                                            "enum": energysegment_ids,
                                        },
                                        "distance": {
                                            "type": "integer",
                                            "minimum": 0,
                                        },
                                        "repetition": {
                                            "type": "integer",
                                            "minimum": 1,
                                        },
                                        "t_start": {
                                            "type": "string",
                                            "pattern": "^[0-9]{2}:[0-9]{2}$",
                                        },
                                        "t_break": {
                                            "type": "string",
                                            "pattern": "^[0-9]{2}:[0-9]{2}$",
                                        },
                                        "notes": {
                                            "type": "string",
                                            "maxLength": 200,
                                        },
                                    },
                                    "required": [
                                        "modality_id",
                                        "energysegment_id",
                                        "distance",
                                        "repetition",
                                    ],
                                },
                            },
                        },
                        "required": ["count", "exercises"],
                    },
                },
                "rationale": {
                    "type": "string",
                    "description": "Overall explanation (3-5 sentences)",
                },
            },
            "required": ["rounds", "rationale"],
        },
    }


def build_system_prompt(sport_name):
    return (
        f"You are an expert coach in {sport_name} training. "
        f"You generate detailed and progressive training sessions using "
        f"ONLY the modalities and energysegments from the provided catalog. "
        f"You MUST always respond using the 'create_training_session' tool. "
        f"Never write free-form text."
    )


def build_user_prompt(*, event, modalities_catalog, energysegments_catalog):
    language = (
        event.refer_program.team.language
        if event.refer_program and event.refer_program.team
        else "fr"
    )
    language_label = resolve_language_label(language)

    cat_modalities = "\n".join(f"  {m['id']}: {m['name']}" for m in modalities_catalog)
    cat_segments = "\n".join(f"  {s['id']}: {s['abv']}" for s in energysegments_catalog)

    return (
        f"Generate the detail of a training session with these constraints:\n"
        f"- Session name: {event.name}\n"
        f"- Goal: {event.goal or '(not specified)'}\n"
        f"- Planned date: {event.date.isoformat() if event.date else '(not specified)'}\n"
        f"- Target total distance: {event.total or 0} meters\n\n"
        f"Authorized modalities catalog (id: name):\n{cat_modalities}\n\n"
        f"Authorized energysegments catalog (id: abv):\n{cat_segments}\n\n"
        f"IMPORTANT instructions:\n"
        f"- The 'Session name' and 'Goal' above are provided by the coach in "
        f"{language_label}. They may contain indications about intensity, "
        f"target athlete population, or equipment to use. Take this into "
        f"account when designing the session.\n"
        f"- Build a structured session with:\n"
        f"  * a warm-up round\n"
        f"  * one or more main rounds\n"
        f"  * a cool-down round\n"
        f"- The sum of (exercise.distance * exercise.repetition * round.count) "
        f"across the whole session must approach {event.total or 0} meters.\n"
        f"- Use ONLY the ids provided in the catalogs.\n"
        f"- Respond ENTIRELY in {language_label}: all notes and the rationale "
        f"must be in {language_label}.\n"
        f"- Use the 'create_training_session' tool only.\n"
    )


def generate_training(*, event):
    from exercise.models import EnergySegment, Modality

    sport = (
        event.refer_program.team.sport if event.refer_program and event.refer_program.team else None
    )
    sport_name = sport.name if sport else "the practiced sport"

    modalities_qs = Modality.objects.filter(sport=sport) if sport else Modality.objects.all()
    modalities = list(modalities_qs.values("id", "name"))
    energysegments = list(EnergySegment.objects.values("id", "abv"))

    if not modalities:
        raise AIServiceError(_("No modalities defined for this sport. Cannot generate."))
    if not energysegments:
        raise AIServiceError(_("No energy segments defined. Cannot generate."))

    modality_ids = [m["id"] for m in modalities]
    energysegment_ids = [s["id"] for s in energysegments]

    tool = build_training_tool_schema(
        modality_ids=modality_ids,
        energysegment_ids=energysegment_ids,
    )
    system = build_system_prompt(sport_name)
    user_prompt = build_user_prompt(
        event=event,
        modalities_catalog=modalities,
        energysegments_catalog=energysegments,
    )

    result = call_claude_with_tool(
        prompt=user_prompt,
        system=system,
        tool=tool,
    )

    tool_input = result["tool_input"]
    rounds_data = tool_input.get("rounds", [])
    rationale = tool_input.get("rationale", "")

    if not isinstance(rounds_data, list) or not rounds_data:
        raise AIServiceError(_("AI returned empty or invalid rounds."))

    valid_modality_ids = set(modality_ids)
    valid_segment_ids = set(energysegment_ids)
    for r in rounds_data:
        for ex in r.get("exercises", []):
            if ex.get("modality_id") not in valid_modality_ids:
                raise AIServiceError(_("AI used an invalid modality id."))
            if ex.get("energysegment_id") not in valid_segment_ids:
                raise AIServiceError(_("AI used an invalid energysegment id."))

    return {
        "rounds": rounds_data,
        "rationale": rationale,
        "prompt_sent": user_prompt,
        "model": result["model"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
    }
