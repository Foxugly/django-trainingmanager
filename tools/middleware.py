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
            user_lang = getattr(request.user, "language", None)
            if user_lang:
                translation.activate(user_lang)
                request.LANGUAGE_CODE = user_lang
        try:
            response = self.get_response(request)
        finally:
            translation.deactivate()
        return response
