from django.utils import translation


class UserLanguageMiddleware:
    """Override request language with user.language for authenticated users.

    Must be installed AFTER AuthenticationMiddleware. Order resolution:
    user.language > Accept-Language > settings.LANGUAGE_CODE.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, "user") and request.user.is_authenticated:
            # I6: CustomUser.language is a guaranteed model field; no need
            # for a defensive getattr that would silently mask a future
            # rename or drop. AnonymousUser is excluded by is_authenticated
            # just above.
            user_lang = request.user.language
            if user_lang:
                translation.activate(user_lang)
                request.LANGUAGE_CODE = user_lang
        try:
            response = self.get_response(request)
        finally:
            translation.deactivate()
        return response
