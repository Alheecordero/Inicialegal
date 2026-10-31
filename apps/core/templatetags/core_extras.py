import re

from django import template
from django.templatetags.static import static
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


@register.simple_tag(takes_context=True)
def legal_service_ld(context):
    """JSON-LD LegalService con los datos de contacto de SiteSettings (para la portada)."""
    import json

    site, site_url = context["site"], context["site_url"]
    data = {
        "@context": "https://schema.org",
        "@type": "LegalService",
        "@id": f"{site_url}/#organizacion",
        "name": site.site_name,
        "url": f"{site_url}/",
        "description": site.meta_description,
        "email": site.email,
        "telephone": site.phone,
        "areaServed": {"@type": "Country", "name": "Chile"},
    }
    data["logo"] = data["image"] = site_url + (site.logo.url if site.logo else static("img/logo.png"))
    if site.address:
        data["address"] = {
            "@type": "PostalAddress",
            "streetAddress": site.address,
            "addressLocality": site.city or "Santiago",
            "addressCountry": "CL",
        }
    if site.map_latitude is not None and site.map_longitude is not None:
        data["geo"] = {"@type": "GeoCoordinates", "latitude": float(site.map_latitude), "longitude": float(site.map_longitude)}
    same_as = [u for u in (site.instagram, site.linkedin, site.facebook, site.tiktok, site.youtube) if u]
    if same_as:
        data["sameAs"] = same_as
    raw = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return mark_safe(f'<script type="application/ld+json">{raw}</script>')
