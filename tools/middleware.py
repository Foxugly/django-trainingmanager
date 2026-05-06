from django.conf import settings
from django.utils import translation


class UserLanguageMiddleware:
    """Override request language with user.language for authenticated users.

    Must be installed AFTER AuthenticationMiddleware. Order resolution:
    user.language > Accept-Language > settings.LANGUAGE_CODE.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Pre-compute the allowed language set once so the per-request
        # check is just a dict lookup.
        self._supported = {code for code, _label in settings.LANGUAGES}

    def __call__(self, request):
        if hasattr(request, "user") and request.user.is_authenticated:
            # I6: CustomUser.language is a guaranteed model field; no need
            # for a defensive getattr that would silently mask a future
            # rename or drop. AnonymousUser is excluded by is_authenticated
            # just above.
            #
            # Defence-in-depth: a user.language outside settings.LANGUAGES
            # would fall through to translation.activate, which would
            # silently install a non-existent locale and return untranslated
            # strings. CustomUser.language already has choices=LANGUAGES so
            # this guard only matters when a user is created bypassing the
            # serializer — but the cost is one set lookup.
            user_lang = request.user.language
            if user_lang and user_lang in self._supported:
                translation.activate(user_lang)
                request.LANGUAGE_CODE = user_lang
        try:
            response = self.get_response(request)
        finally:
            translation.deactivate()
        return response
