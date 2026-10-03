from django.conf import settings
from django.utils import translation

ADMIN_LANG_COOKIE = "kimame_admin_lang"
ADMIN_LANGUAGES = ("ja", "es")


class AdminLanguageMiddleware:
    """Let staff switch the admin between Japanese and Spanish.

    The storefront always stays Japanese; only requests under the admin path pick
    up the language chosen with the switcher (kept in a cookie).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_prefix = "/" + settings.ADMIN_URL_PATH

    def __call__(self, request):
        if not request.path.startswith(self.admin_prefix):
            return self.get_response(request)

        lang = request.COOKIES.get(ADMIN_LANG_COOKIE)
        if lang not in ADMIN_LANGUAGES:
            lang = settings.LANGUAGE_CODE
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        try:
            response = self.get_response(request)
        finally:
            translation.deactivate()
        response.headers.setdefault("Content-Language", lang)
        return response
