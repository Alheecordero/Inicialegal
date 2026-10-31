from django.conf import settings
from django.http import HttpResponse
from django.utils import translation

from . import ratelimit


class SiteLocaleMiddleware:
    """Sitio público solo en español; redirige /en/ al equivalente sin prefijo."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.admin = "/" + settings.ADMIN_PATH.strip("/")

    def __call__(self, request):
        path = request.path or "/"
        if path == "/en" or path.startswith("/en/"):
            from django.http import HttpResponsePermanentRedirect

            target = path[3:] or "/"
            query = request.META.get("QUERY_STRING", "")
            if query:
                target = f"{target}?{query}"
            return HttpResponsePermanentRedirect(target)
        translation.activate("es-cl")
        request.LANGUAGE_CODE = "es-cl"
        return self.get_response(request)


class NoIndexMiddleware:
    """Mientras SITE_INDEXING=False, pide a buscadores no indexar ninguna respuesta."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not settings.SITE_INDEXING:
            response["X-Robots-Tag"] = "noindex, nofollow, noarchive, nosnippet"
        return response


class AdminLoginThrottleMiddleware:
    """Tras varios intentos fallidos, el inicio de sesión del panel responde 429 un rato."""

    MAX_FAILS = 5
    WINDOW = 15 * 60

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        login_path = "/" + settings.ADMIN_PATH.strip("/") + "/login/"
        if request.path != login_path or request.method != "POST":
            return self.get_response(request)
        key = "admin-fail:" + ratelimit.client_ip(request)
        if ratelimit.peek(key) >= self.MAX_FAILS:
            return HttpResponse("Demasiados intentos. Espere unos minutos e inténtelo de nuevo.", status=429)
        response = self.get_response(request)
        location = response.get("Location", "")
        if response.status_code == 302 and "login" not in location:
            ratelimit.reset(key)
        elif response.status_code == 200:
            ratelimit.hit(key, self.MAX_FAILS, self.WINDOW)
        return response
