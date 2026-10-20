"""Textos comerciales del sitio (fuente única para seed y refresh en producción)."""

from apps.core.corporativo_content import CORPORATIVO_SHORT as _CORP_SHORT
from apps.core.models import HeroSlide, Plan, PracticeArea, SiteSettings
from apps.core.tecnologia_datos_content import TECNOLOGIA_DATOS_SHORT as _TEC_SHORT

ABOUT_TEXT = (
    "<p><strong>Inicia Legal</strong> es un estudio jurídico corporativo en Santiago. Asesoramos a "
    "<strong>emprendedores, e-commerce, startups y pymes en crecimiento</strong>, así como a socios y "
    "administradores, en las materias que definen la operación diaria.</p>"
    "<p><strong>Cómo trabajamos:</strong> comprendemos su negocio, ordenamos el riesgo jurídico y "
    "entregamos una recomendación aplicable, con un <strong>equipo multidisciplinario en una sola "
    "conversación</strong> (societario, laboral, tributario, penal económico y compliance, protección "
    "de datos y propiedad industrial).</p>"
    "<p>Nuestra práctica se funda en prevenir antes de corregir: acompañamos de manera permanente en "
    "contratos, relaciones laborales, estructuración societaria y cumplimiento normativo, desde la "
    "constitución hasta reorganizaciones y operaciones relevantes.</p>"
    "<p>Cada asunto es conducido por abogados especializados, con rigor técnico y comprensión cercana "
    "de la realidad de su empresa.</p>"
)

SITE_FIELDS = {
    "tagline": "Respaldo legal anual para pymes y empresas en crecimiento en Chile",
    "hero_kicker": "Estudio jurídico para pymes y empresas en crecimiento",
    "hero_title": "Respaldo legal *con criterio de negocio*",
    "hero_subtitle": (
        "Equipo integral en societario, contratos, laboral, tributario, compliance y datos. "
        "Planes anuales desde 5 UF mensuales + IVA. Atención presencial en Santiago y remota en todo Chile."
    ),
    "hero_primary_text": "Agende una conversación inicial",
    "hero_primary_url": "/contacto/",
    "hero_secondary_text": "Ver planes desde 5 UF",
    "hero_secondary_url": "/planes/",
    "about_kicker": "Quiénes somos",
    "about_title": "Un equipo jurídico que previene antes de corregir",
    "about_text": ABOUT_TEXT,
    "cta_title": "¿Su empresa toma decisiones legales a tiempo?",
    "cta_text": (
        "Conversemos sobre su situación jurídica. La primera reunión no tiene costo. "
        "Atención presencial en Santiago y remota en todo Chile."
    ),
    "cta_button_text": "Agende una conversación",
    "cta_button_url": "/contacto/",
    "meta_description": (
        "Estudio jurídico en Santiago. Respaldo legal anual para pymes: societario, laboral, "
        "tributario, compliance y planes desde 5 UF mensuales."
    ),
    "meta_keywords": (
        "abogados empresas Chile, asesoría legal pymes, plan legal, compliance, gobierno corporativo, Santiago"
    ),
    "footer_text": (
        "Estudio jurídico corporativo en Santiago. Respaldo legal anual, cumplimiento normativo y "
        "equipo multidisciplinario para empresas en crecimiento."
    ),
}

HERO_SLIDES = {
    "principal": {
        "kicker": "Estudio jurídico para pymes y empresas en crecimiento",
        "title": "Respaldo legal *con criterio de negocio*",
        "subtitle": SITE_FIELDS["hero_subtitle"],
        "primary_text": "Agende una conversación inicial",
        "primary_url": "/contacto/",
        "secondary_text": "Ver planes desde 5 UF",
        "secondary_url": "/planes/",
    },
    "planes": {
        "kicker": "Planes anuales",
        "title": "Respaldo *durante todo el año*",
        "subtitle": (
            "Plan Legal Pyme (desde 5 UF mensuales + IVA) para respaldo recurrente. "
            "Plan Legal Advance si necesita más contratos a medida y cobertura de juicio laboral."
        ),
        "primary_text": "Compare nuestros planes",
        "primary_url": "/planes/",
        "secondary_text": "Agende una conversación inicial",
        "secondary_url": "/contacto/",
    },
}

AREA_SHORTS = {
    "corporativo": _CORP_SHORT,
    "derecho-laboral": (
        "Cumplimiento laboral y defensa de contingencias para operar con equipos en regla."
    ),
    "derecho-tributario": (
        "Planificación y regularización ante el SII con decisiones tributarias claras."
    ),
    "derecho-penal-economico": (
        "Compliance y prevención de delitos para reducir el riesgo penal de la empresa."
    ),
    "tecnologia-y-datos": _TEC_SHORT,
    "propiedad-industrial": (
        "Registro y defensa de marcas para proteger la identidad comercial."
    ),
}

PLAN_TAGLINES = {
    "plan-legal-pyme": (
        "Ideal si su empresa necesita respaldo legal recurrente, revisión de contratos y "
        "auditoría laboral semestral."
    ),
    "plan-legal-advance": (
        "Recomendado si requiere mayor volumen de contratos a medida y cobertura de un "
        "juicio laboral ordinario o monitorio."
    ),
}


def apply_site_settings():
    site = SiteSettings.load()
    for field, value in SITE_FIELDS.items():
        setattr(site, field, value)
    site.save()
    return site


def apply_hero_slides():
    updated = 0
    for key, fields in HERO_SLIDES.items():
        slide = HeroSlide.objects.filter(key=key).first()
        if not slide:
            continue
        for field, value in fields.items():
            setattr(slide, field, value)
        slide.save()
        updated += 1
    return updated


def apply_area_shorts():
    updated = 0
    for slug, short in AREA_SHORTS.items():
        n = PracticeArea.objects.filter(slug=slug).update(short_description=short)
        updated += n
    return updated


def apply_plan_taglines():
    updated = 0
    for slug, tagline in PLAN_TAGLINES.items():
        n = Plan.objects.filter(slug=slug).update(tagline=tagline)
        updated += n
    return updated


def apply_all():
    apply_site_settings()
    slides = apply_hero_slides()
    areas = apply_area_shorts()
    plans = apply_plan_taglines()
    return {"hero_slides": slides, "areas": areas, "plans": plans}
