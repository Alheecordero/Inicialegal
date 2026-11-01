import re

from django import template
from django.templatetags.static import static
from django.utils.html import escape, strip_tags
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


def _ld_script(data):
    """<script> JSON-LD seguro dentro de HTML."""
    import json

    raw = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return mark_safe(f'<script type="application/ld+json">{raw}</script>')


def _org_ref(context):
    site, site_url = context["site"], context["site_url"]
    return {"@type": "LegalService", "@id": f"{site_url}/#organizacion", "name": site.site_name, "url": f"{site_url}/"}


def _abs(context, url):
    return context["site_url"] + url if url else ""


@register.simple_tag(takes_context=True)
def legal_service_ld(context):
    """JSON-LD LegalService con los datos de contacto de SiteSettings (para la portada)."""
    site, site_url = context["site"], context["site_url"]
    data = {
        "@context": "https://schema.org",
        **_org_ref(context),
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
    return _ld_script(data)


@register.simple_tag(takes_context=True)
def breadcrumb_ld(context, *crumbs):
    """Migas de pan: pares título, URL relativa; el último elemento puede ir sin URL (página actual)."""
    items = [("Inicio", "/")]
    pairs = list(crumbs)
    while pairs:
        title = pairs.pop(0)
        url = pairs.pop(0) if pairs else context["request"].path
        items.append((title, url or context["request"].path))
    return _ld_script({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": str(title), "item": _abs(context, url)}
            for i, (title, url) in enumerate(items, start=1)
        ],
    })


@register.simple_tag(takes_context=True)
def service_ld(context, obj, service_type=""):
    """Service para fichas de servicio y de área de práctica."""
    data = {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": obj.name,
        "description": obj.short_description,
        "url": _abs(context, obj.get_absolute_url()),
        "provider": _org_ref(context),
        "areaServed": {"@type": "Country", "name": "Chile"},
        "audience": {"@type": "BusinessAudience", "name": "Empresas y pymes"},
    }
    if service_type:
        data["serviceType"] = service_type
    if getattr(obj, "image", None):
        data["image"] = _abs(context, obj.image.url)
    return _ld_script(data)


@register.simple_tag(takes_context=True)
def plan_ld(context, plan):
    """Service con Offer para un plan; el UF se informa con su código ISO 4217 (CLF)."""
    data = {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": plan.name,
        "description": plan.summary or plan.tagline,
        "url": _abs(context, plan.get_absolute_url()),
        "provider": _org_ref(context),
        "areaServed": {"@type": "Country", "name": "Chile"},
        "audience": {"@type": "BusinessAudience", "name": "Empresas y pymes"},
    }
    if plan.price_annual:
        currency = "CLF" if plan.currency == "UF" else plan.currency
        data["offers"] = {
            "@type": "Offer",
            "price": str(plan.price_annual),
            "priceCurrency": currency,
            "priceSpecification": {
                "@type": "UnitPriceSpecification",
                "price": str(plan.price_annual),
                "priceCurrency": currency,
                "unitText": "año",
                "valueAddedTaxIncluded": "IVA" not in (plan.price_suffix or ""),
            },
            "url": _abs(context, plan.get_absolute_url()),
        }
    return _ld_script(data)


@register.simple_tag(takes_context=True)
def person_ld(context, member):
    data = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": member.name,
        "jobTitle": member.role,
        "url": _abs(context, member.get_absolute_url()),
        "worksFor": _org_ref(context),
    }
    if member.photo:
        data["image"] = _abs(context, member.photo.url)
    if member.specialty:
        data["knowsAbout"] = member.specialty
    if member.linkedin:
        data["sameAs"] = [member.linkedin]
    return _ld_script(data)


@register.simple_tag
def faq_ld(faqs):
    """FAQPage a partir de objetos con question/answer (las mismas preguntas visibles en la página)."""
    faqs = [f for f in faqs if f.question and f.answer]
    if not faqs:
        return ""
    return _ld_script({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": f.question, "acceptedAnswer": {"@type": "Answer", "text": strip_tags(f.answer)}}
            for f in faqs
        ],
    })
