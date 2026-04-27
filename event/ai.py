"""AI-driven training session generation for an Event."""

import logging

from tools.ai import AIServiceError, call_claude_with_tool

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
        f"Tu es un coach expert en planification d'entrainement de {sport_name}. "
        f"Tu generes des seances detaillees et progressives en utilisant UNIQUEMENT "
        f"les modalities et energysegments fournis dans le catalogue. "
        f"Tu DOIS toujours repondre en utilisant le tool 'create_training_session'. "
        f"N'ecris jamais de texte libre."
    )


def build_user_prompt(*, event, modalities_catalog, energysegments_catalog):
    cat_modalities = "\n".join(f"  {m['id']}: {m['name']}" for m in modalities_catalog)
    cat_segments = "\n".join(f"  {s['id']}: {s['abv']}" for s in energysegments_catalog)

    return (
        f"Genere le detail d'une seance d'entrainement avec ces contraintes :\n"
        f"- Nom de la seance : {event.name}\n"
        f"- Objectif : {event.goal or '(non precise)'}\n"
        f"- Date prevue : {event.date.isoformat() if event.date else '(non precisee)'}\n"
        f"- Distance totale visee : {event.total or 0} metres\n\n"
        f"Catalogue de modalities autorisees (id: name) :\n{cat_modalities}\n\n"
        f"Catalogue d'energysegments autorises (id: abv) :\n{cat_segments}\n\n"
        f"Construis une seance structuree avec :\n"
        f"- Un round d'echauffement\n"
        f"- Un ou plusieurs rounds de corps de seance\n"
        f"- Un round de retour au calme\n"
        f"\nLa somme des distances de tous les exercises x leur repetition x le count "
        f"de leur round doit approcher {event.total or 0} metres.\n"
        f"Utilise UNIQUEMENT les ids fournis dans les catalogues."
    )


def generate_training(*, event):
    from exercise.models import EnergySegment, Modality

    sport = (
        event.refer_program.team.sport if event.refer_program and event.refer_program.team else None
    )
    sport_name = sport.name if sport else "le sport pratique"

    modalities_qs = Modality.objects.filter(sport=sport) if sport else Modality.objects.all()
    modalities = list(modalities_qs.values("id", "name"))
    energysegments = list(EnergySegment.objects.values("id", "abv"))

    if not modalities:
        raise AIServiceError(f"No modalities defined for sport {sport_name}. Cannot generate.")
    if not energysegments:
        raise AIServiceError("No energy segments defined. Cannot generate.")

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
        raise AIServiceError("AI returned empty or invalid rounds.")

    valid_modality_ids = set(modality_ids)
    valid_segment_ids = set(energysegment_ids)
    for r in rounds_data:
        for ex in r.get("exercises", []):
            if ex.get("modality_id") not in valid_modality_ids:
                raise AIServiceError(f"AI used invalid modality_id: {ex.get('modality_id')}")
            if ex.get("energysegment_id") not in valid_segment_ids:
                raise AIServiceError(
                    f"AI used invalid energysegment_id: {ex.get('energysegment_id')}"
                )

    return {
        "rounds": rounds_data,
        "rationale": rationale,
        "prompt_sent": user_prompt,
        "model": result["model"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
    }
