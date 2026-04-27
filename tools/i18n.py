from django.conf import settings

DEFAULT_PROMPT_LANGUAGE = "fr"


def resolve_language_label(language_code):
    """Return the native label of a language code from settings.LANGUAGES.

    For unknown codes, falls back to the project's default prompt language
    (Team/User default = 'fr'), then ultimately to 'Français'.
    """
    mapping = dict(settings.LANGUAGES)
    if language_code in mapping:
        return mapping[language_code]
    return mapping.get(DEFAULT_PROMPT_LANGUAGE, "Français")
