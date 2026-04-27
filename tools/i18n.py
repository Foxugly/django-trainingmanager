from django.conf import settings


def resolve_language_label(language_code):
    """Return the native label of a language code from settings.LANGUAGES.

    Falls back to the LANGUAGE_CODE default's label when the code is unknown,
    and ultimately to 'Français' if neither resolves.
    """
    mapping = dict(settings.LANGUAGES)
    if language_code in mapping:
        return mapping[language_code]
    return mapping.get(settings.LANGUAGE_CODE, "Français")
