import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import get_language

register = template.Library()

# Iconos de contenido (áreas, servicios, planes, cifras) en trazo fino de Phosphor.
# Los nombres se guardan como clases de Bootstrap Icons; este mapa los traduce.
_PHOSPHOR = {
    "bi-briefcase": "briefcase",
    "bi-people": "users-three",
    "bi-people-fill": "users-three",
    "bi-calculator": "calculator",
    "bi-shield-lock": "shield-check",
    "bi-file-earmark-text": "file-text",
    "bi-pencil-square": "note-pencil",
    "bi-chat-dots": "chat-circle-dots",
    "bi-clipboard-check": "clipboard-text",
    "bi-bank": "bank",
    "bi-person-badge": "identification-badge",
    "bi-building": "buildings",
    "bi-award": "seal-check",
    "bi-laptop": "laptop",
    "bi-grid": "squares-four",
    "bi-calendar-check": "calendar-check",
    "bi-percent": "percent",
    "bi-globe": "globe",
    "bi-shield": "shield",
}

_ACCENT = re.compile(r"\*(.+?)\*")


@register.filter
def ph(value):
    """Traduce una clase bi-* a su equivalente Phosphor (trazo fino). Si no hay equivalente, conserva Bootstrap Icons."""
    name = _PHOSPHOR.get((value or "").strip())
    return f"ph-light ph-{name}" if name else f"bi {value}"


@register.filter
def accent(value):
    """Convierte *texto* en <em>texto</em> (destacado dorado) escapando el resto del contenido.

    Permite que desde el administrador se marque qué parte de un título se resalta,
    por ejemplo: "Soluciones legales para empresas que *quieren crecer*".
    """
    if not value:
        return ""
    return mark_safe(_ACCENT.sub(r"<em>\1</em>", escape(value)))


@register.filter
def strip_accent(value):
    """Quita los marcadores *...* (para meta tags y atributos alt)."""
    return _ACCENT.sub(r"\1", value or "")


@register.filter
def localized_href(url):
    """Antepone /en a una ruta interna cuando el visitante está en inglés."""
    if not url or not isinstance(url, str):
        return url or ""
    if url.startswith(("http://", "https://", "mailto:", "tel:", "#")):
        return url
    lang = get_language() or ""
    if not lang.startswith("en"):
        return url
    if url == "/en" or url.startswith("/en/") or url.startswith("/en?"):
        return url
    if url.startswith("/"):
        return "/en" + url
    return url
