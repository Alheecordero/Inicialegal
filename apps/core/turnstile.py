"""Cloudflare Turnstile (anti-bots) para los formularios públicos.

Se activa solo si TURNSTILE_SITE_KEY y TURNSTILE_SECRET_KEY están definidas; sin ellas todo pasa.
"""
import json
import logging
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from django.conf import settings

from .ratelimit import client_ip

logger = logging.getLogger(__name__)

VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def enabled():
    return bool(settings.TURNSTILE_SITE_KEY and settings.TURNSTILE_SECRET_KEY)


def verify(request):
    """True si el token del formulario es válido (o si Turnstile está apagado)."""
    if not enabled():
        return True
    token = request.POST.get("cf-turnstile-response", "")
    if not token or len(token) > 2048:
        return False
    body = urlencode({"secret": settings.TURNSTILE_SECRET_KEY, "response": token, "remoteip": client_ip(request)})
    try:
        with urlopen(VERIFY_URL, data=body.encode(), timeout=5) as resp:
            result = json.load(resp)
    except (URLError, TimeoutError, ValueError) as exc:
        # Si Cloudflare no responde no se pierden contactos: siguen los límites por IP y el honeypot.
        logger.warning("Turnstile no respondió: %s", exc)
        return True
    if not result.get("success"):
        logger.info("Turnstile rechazó un envío: %s", result.get("error-codes"))
    return bool(result.get("success"))
