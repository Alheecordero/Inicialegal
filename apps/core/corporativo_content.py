"""Corporativo: fuente única para la ficha del área y los servicios del formulario de contacto."""

from django.utils.text import slugify

CORPORATIVO_AREA_SLUG = "corporativo"

CORPORATIVO = {
    "short": "Derecho societario, contratación comercial, transacciones y litigación civil y comercial.",
    "intro": [
        (
            "El grupo Corporativo asesora a empresas en la estructuración, el funcionamiento y el crecimiento "
            "de sus sociedades, así como en las relaciones contractuales que sostienen su operación. Acompañamos "
            "a nuestros clientes desde la constitución de la sociedad hasta sus procesos de inversión, "
            "reorganización o venta, y los representamos cuando sus intereses deben defenderse ante los tribunales."
        ),
        (
            "Nuestra asesoría se coordina con los grupos Tributario, Laboral y Penal Económico y Compliance, "
            "de modo que cada decisión societaria o contractual considere sus efectos en todas las materias "
            "de la empresa."
        ),
    ],
    "services_heading": "Servicios corporativos",
    "sections": [
        {
            "title": "Derecho societario",
            "lead_em": "Estructuramos y mantenemos en regla la organización jurídica de la empresa.",
            "icon": "bi-building",
            "items": [
                ("soc-constitucion", "Constitución, modificación, transformación, fusión, división, disolución y liquidación de sociedades."),
                ("soc-capital", "Aumentos y disminuciones de capital, incluidos los aportes en especie."),
                ("soc-cesion", "Cesión de derechos sociales, traspaso de acciones e incorporación y retiro de socios."),
                ("soc-pactos", "Pactos de accionistas y de socios."),
                ("soc-juntas", "Juntas de accionistas, sesiones de directorio, actas y libros societarios."),
                ("soc-gobierno", "Administración, poderes y gobierno corporativo."),
                ("soc-inscripciones", "Inscripciones y publicaciones en el Conservador de Bienes Raíces y en el Diario Oficial."),
            ],
        },
        {
            "title": "Inversión, reorganizaciones y transacciones",
            "lead": "Asesoramos a la empresa en las operaciones que transforman su estructura o su propiedad.",
            "icon": "bi-briefcase",
            "items": [
                ("inv-rondas", "Rondas de inversión y documentación de aumentos de capital con nuevos accionistas."),
                ("inv-reorg", "Reorganizaciones societarias y salida de socios."),
                ("inv-compraventa", "Compraventa de acciones, derechos sociales y empresas."),
                ("inv-dd", "Due diligence legal para procesos de inversión y compraventa."),
            ],
        },
        {
            "title": "Contratación comercial",
            "lead": "Redactamos, revisamos y negociamos los contratos que sostienen la operación de la empresa.",
            "icon": "bi-file-earmark-text",
            "items": [
                ("ctr-comercial", "Contratos de prestación de servicios, suministro, distribución, agencia, franquicia, compraventa y arrendamiento comercial."),
                ("ctr-tech", "Contratos tecnológicos: desarrollo de software, licencias y servicios en la nube."),
                ("ctr-nda", "Acuerdos de confidencialidad."),
                ("ctr-licitaciones", "Revisión de bases y contratos tipo en licitaciones."),
                ("ctr-cgc", "Condiciones generales de contratación con clientes y proveedores."),
            ],
        },
        {
            "title": "Consumo y comercio electrónico",
            "icon": "bi-cart",
            "items": [
                ("cons-normativa", "Cumplimiento de la normativa de protección de los derechos de los consumidores."),
                ("cons-terminos", "Términos y condiciones de tiendas en línea y plataformas digitales."),
                ("cons-sernac", "Gestión de reclamos y procedimientos ante el SERNAC y los juzgados de policía local."),
            ],
        },
        {
            "title": "Cobranza, garantías e insolvencia",
            "icon": "bi-bank",
            "items": [
                ("cob-garantias", "Pagarés, reconocimientos de deuda, convenios de pago y constitución de garantías."),
                ("cob-judicial", "Cobranza extrajudicial y judicial; juicios ejecutivos, como demandante y en la defensa del ejecutado."),
                ("cob-concursal", "Procedimientos concursales de reorganización y liquidación de empresas."),
            ],
        },
        {
            "title": "Litigación civil y comercial",
            "icon": "bi-bank",
            "items": [
                ("lit-juicios", "Representación judicial de la empresa en juicios civiles y comerciales."),
                ("lit-mediacion", "Mediación y negociación con terceros."),
            ],
        },
    ],
}


def _service_slug(key: str) -> str:
    return f"corporativo-{key}"


def _service_name(text: str) -> str:
    text = text.strip()
    if len(text) <= 120:
        return text
    return text[:117].rstrip() + "…"


def build_corporativo_html() -> str:
    parts = []
    for para in CORPORATIVO["intro"]:
        parts.append(f"<p>{para}</p>")
    heading = CORPORATIVO.get("services_heading")
    if heading:
        parts.append(f'<h2 class="h3 mt-5 mb-4">{heading}</h2>')
    for section in CORPORATIVO["sections"]:
        parts.append(f"<h3>{section['title']}</h3>")
        lead = section.get("lead_em") or section.get("lead")
        if lead:
            parts.append(f"<p><em>{lead}</em></p>")
        parts.append("<ul>")
        for _key, text in section["items"]:
            parts.append(f"<li>{text}</li>")
        parts.append("</ul>")
    return "".join(parts)


def sync_corporativo(*, stdout=None):
    """Actualiza la ficha Corporativo y los servicios activos vinculados al área."""
    from apps.core.models import PracticeArea, Service

    area = PracticeArea.objects.filter(slug=CORPORATIVO_AREA_SLUG).first()
    if area is None:
        raise RuntimeError(f"No existe el área con slug «{CORPORATIVO_AREA_SLUG}».")

    html = build_corporativo_html()
    area.short_description = CORPORATIVO["short"]
    area.description = html
    update_fields = ["short_description", "description"]
    if hasattr(area, "description_es_cl"):
        area.description_es_cl = html
        area.short_description_es_cl = CORPORATIVO["short"]
        update_fields += ["description_es_cl", "short_description_es_cl"]
    area.save(update_fields=update_fields)

    synced_slugs = []
    order = 0
    for section in CORPORATIVO["sections"]:
        icon = section.get("icon", "bi-building")
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
                    "is_featured": order < 6,
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
            f"· Corporativo: ficha actualizada, {len(synced_slugs)} servicios activos"
            + (f", {deactivated} servicios anteriores desactivados" if deactivated else "")
        )
    return len(synced_slugs)


# Compatibilidad con imports previos
CORPORATIVO_SHORT = CORPORATIVO["short"]
CORPORATIVO_DESCRIPTION = build_corporativo_html()
