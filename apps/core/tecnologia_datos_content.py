"""Tecnología y datos: fuente única para la ficha del área y servicios del contacto."""

AREA_SLUG = "tecnologia-y-datos"
SERVICE_SLUG_PREFIX = "tecnologia-datos"

TECNOLOGIA_DATOS = {
    "short": "Protección de datos personales y ciberseguridad de la empresa.",
    "intro": [
        "Acompañamos a la empresa en el régimen de datos personales y en los contratos de su operación tecnológica.",
    ],
    "services_heading": "Servicios en tecnología y datos",
    "sections": [
        {
            "title": "Protección de datos personales",
            "lead": (
                "Diseñamos e implementamos programas de adecuación a la Ley N.° 21.719, proporcionales al tamaño "
                "y a la actividad de cada empresa."
            ),
            "icon": "bi-shield-lock",
            "items": [
                ("dpd-diagnostico", "Diagnóstico de brechas de cumplimiento y plan de adecuación."),
                ("dpd-inventario", "Inventario y registro de las actividades de tratamiento de datos."),
                ("dpd-licitud", "Determinación de las bases de licitud de cada tratamiento."),
                ("dpd-politicas", "Políticas de privacidad, avisos de información y cláusulas de consentimiento."),
                (
                    "dpd-derechos",
                    "Procedimientos para la atención de los derechos de los titulares: acceso, rectificación, "
                    "supresión, oposición, portabilidad y bloqueo.",
                ),
                (
                    "dpd-encargados",
                    "Contratos con encargados de tratamiento y regulación de las transferencias internacionales de datos.",
                ),
                ("dpd-eipd", "Evaluaciones de impacto en protección de datos."),
                ("dpd-brechas", "Protocolos de gestión y notificación de vulneraciones de seguridad."),
                ("dpd-delegado", "Modelos de prevención de infracciones y asesoría al delegado de protección de datos."),
                (
                    "dpd-trabajadores",
                    "Tratamiento de datos de trabajadores: sistemas de control de asistencia, biometría y videovigilancia.",
                ),
                ("dpd-marketing", "Bases de datos comerciales y comunicaciones de marketing."),
                ("dpd-agencia", "Representación de la empresa ante la Agencia de Protección de Datos Personales."),
            ],
        },
        {
            "title": "Ciberseguridad",
            "lead": (
                "Asesoramos a la empresa en el cumplimiento de la Ley N.° 21.663, Marco de Ciberseguridad, "
                "y en la gestión legal de los incidentes que afecten sus sistemas."
            ),
            "icon": "bi-laptop",
            "items": [
                (
                    "cyb-clasificacion",
                    "Determinación de si la empresa es un prestador de servicios esenciales, un operador de importancia "
                    "vital o proveedor de alguno de ellos.",
                ),
                ("cyb-politicas", "Políticas de seguridad de la información y protocolos de respuesta a incidentes."),
                ("cyb-reporte", "Procedimientos de reporte de incidentes ante la autoridad."),
                ("cyb-clausulas", "Cláusulas de ciberseguridad en contratos con clientes y proveedores."),
                (
                    "cyb-incidente",
                    "Asesoría legal durante un incidente, coordinada con la notificación de vulneraciones de datos personales.",
                ),
                ("cyb-delitos", "Delitos informáticos, en conjunto con el grupo Penal Económico y Compliance."),
            ],
        },
        {
            "title": "Contratación tecnológica y plataformas digitales",
            "icon": "bi-cloud",
            "items": [
                ("tech-contratos", "Contratos de desarrollo de software, licencias, servicios en la nube y soporte tecnológico."),
                ("tech-nda", "Acuerdos de confidencialidad en proyectos tecnológicos."),
                ("tech-terminos", "Términos y condiciones de tiendas en línea, aplicaciones y plataformas digitales."),
                ("tech-cookies", "Políticas de cookies y cumplimiento en comunicaciones comerciales electrónicas."),
                ("tech-firma", "Documentos y contratos con firma electrónica."),
            ],
        },
    ],
}


def _service_slug(key: str) -> str:
    return f"{SERVICE_SLUG_PREFIX}-{key}"


def _service_name(text: str) -> str:
    text = text.strip()
    if len(text) <= 120:
        return text
    return text[:117].rstrip() + "…"


def build_tecnologia_datos_html() -> str:
    parts = []
    for para in TECNOLOGIA_DATOS["intro"]:
        parts.append(f"<p>{para}</p>")
    heading = TECNOLOGIA_DATOS.get("services_heading")
    if heading:
        parts.append(f'<h2 class="h3 mt-5 mb-4">{heading}</h2>')
    for section in TECNOLOGIA_DATOS["sections"]:
        parts.append(f"<h3>{section['title']}</h3>")
        lead = section.get("lead_em") or section.get("lead")
        if lead:
            parts.append(f"<p><em>{lead}</em></p>")
        parts.append("<ul>")
        for _key, text in section["items"]:
            parts.append(f"<li>{text}</li>")
        parts.append("</ul>")
    return "".join(parts)


def sync_tecnologia_datos(*, stdout=None):
    from apps.core.models import PracticeArea, Service

    area = PracticeArea.objects.filter(slug=AREA_SLUG).first()
    if area is None:
        raise RuntimeError(f"No existe el área con slug «{AREA_SLUG}».")

    html = build_tecnologia_datos_html()
    area.short_description = TECNOLOGIA_DATOS["short"]
    area.description = html
    update_fields = ["short_description", "description"]
    if hasattr(area, "description_es_cl"):
        area.description_es_cl = html
        area.short_description_es_cl = TECNOLOGIA_DATOS["short"]
        update_fields += ["description_es_cl", "short_description_es_cl"]
    area.save(update_fields=update_fields)

    synced_slugs = []
    order = 0
    for section in TECNOLOGIA_DATOS["sections"]:
        icon = section.get("icon", "bi-laptop")
        section_title = section["title"]
        for key, text in section["items"]:
            slug = _service_slug(key)
            name = _service_name(text)
            short = text[:255]
            desc = (
                f"<p><strong>{section_title}</strong></p>"
                f"<p>{text}</p>"
                f"<p>Solicite una reunión para recibir una propuesta acorde a la empresa.</p>"
            )
            Service.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "icon": icon,
                    "area": area,
                    "short_description": short,
                    "description": desc,
                    "is_active": True,
                    "is_featured": False,
                    "order": order,
                    "price_note": "Cotizar",
                },
            )
            synced_slugs.append(slug)
            order += 1

    deactivated = (
        Service.objects.filter(area=area)
        .exclude(slug__in=synced_slugs)
        .update(is_active=False)
    )

    if stdout is not None:
        stdout.write(
            f"· Tecnología y datos: ficha actualizada, {len(synced_slugs)} servicios activos"
            + (f", {deactivated} desactivados" if deactivated else "")
        )
    return len(synced_slugs)


TECNOLOGIA_DATOS_SHORT = TECNOLOGIA_DATOS["short"]
TECNOLOGIA_DATOS_DESCRIPTION = build_tecnologia_datos_html()
