"""
Carga contenido inicial del sitio a partir de la propuesta comercial
"Plan Legal Advance" de Inicia Legal. Es idempotente: se puede ejecutar
varias veces sin duplicar registros.

    python manage.py seed            # contenido
    python manage.py seed --admin    # además crea superusuario admin/admin1234 si no existe
"""
import re
from datetime import datetime
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone

SEED_MEDIA = Path(__file__).resolve().parents[2] / "seed_media"
SEED_STEMS = {p.stem for p in SEED_MEDIA.iterdir() if p.suffix.lower() in {".jpg", ".pdf"}}
_SUFFIX = re.compile(r"_[A-Za-z0-9]{7}$")  # sufijo aleatorio que Django agrega ante colisiones de nombre


def _seed_stem(field):
    """Devuelve el nombre base si el archivo del campo proviene de seed_media; None si lo subió el cliente."""
    stem = _SUFFIX.sub("", Path(field.name).stem)
    return stem if stem in SEED_STEMS else None


def attach_image(instance, field_name, filename, save=True):
    """Sincroniza una imagen de seed_media con el campo.

    - Si el campo tiene un archivo subido por el cliente, no se toca.
    - Si está vacío o tiene una imagen de seed distinta (o desactualizada), se reemplaza.
    - Si `filename` es None y el campo tiene una imagen de seed, se quita (evita repeticiones).
    """
    field = getattr(instance, field_name)
    if field and _seed_stem(field) is None:
        return False  # imagen del cliente
    path = SEED_MEDIA / filename if filename else None
    if field:
        same = path is not None and _seed_stem(field) == path.stem
        if same:
            try:
                if field.size == path.stat().st_size:
                    return False  # ya está al día
            except (FileNotFoundError, OSError):
                pass
        field.delete(save=False)
    if path is None or not path.exists():
        if filename is None:
            instance.save(update_fields=[field_name])
        return False
    with path.open("rb") as fh:
        field.save(path.name, File(fh), save=save)
    return True

from apps.blog.models import Category, Post, Tag
from apps.core.corporativo_content import CORPORATIVO_SHORT, build_corporativo_html, sync_corporativo
from apps.core.tecnologia_datos_content import (
    TECNOLOGIA_DATOS_SHORT,
    build_tecnologia_datos_html,
    sync_tecnologia_datos,
)
from apps.core.models import (
    FAQ,
    Page,
    Plan,
    PlanBenefit,
    PlanFeature,
    PracticeArea,
    Service,
    SiteSettings,
    Stat,
    TeamMember,
    HeroSlide,
    Testimonial,
)


class Command(BaseCommand):
    help = "Carga contenido inicial (idempotente) para inicialegal.cl"

    def add_arguments(self, parser):
        parser.add_argument("--admin", action="store_true", help="Crear superusuario admin/admin1234 si no existe ninguno.")

    def handle(self, *args, **options):
        self.seed_settings()
        areas = self.seed_areas()
        sync_corporativo(stdout=self.stdout)
        sync_tecnologia_datos(stdout=self.stdout)
        self.seed_services(areas)
        plans = self.seed_plan()
        self.seed_stats()
        self.seed_faqs(plans)
        self.seed_team(areas)
        self.seed_hero()
        self.seed_testimonials()
        self.seed_pages()
        self.seed_blog(areas)
        self._sin_negocio()
        from django.conf import settings

        if any(code == "en" for code, _ in settings.LANGUAGES):
            from apps.core.english_content import apply_english

            apply_english(self.stdout)
        if options["admin"]:
            self.seed_admin()
        self.stdout.write(self.style.SUCCESS("Contenido inicial cargado correctamente."))

    def _sin_negocio(self):
        """Sustituye «negocio» por «empresa» en todo el contenido publicado."""
        from django.apps import apps

        rules = (
            (re.compile(r"\bnegocios\b", re.I), "empresas"),
            (re.compile(r"\bel negocio\b", re.I), "la empresa"),
            (re.compile(r"\bal negocio\b", re.I), "a la empresa"),
            (re.compile(r"\bdel negocio\b", re.I), "de la empresa"),
            (re.compile(r"\bnegocio\b", re.I), "empresa"),
        )

        def reemplazar(text):
            for pattern, repl in rules:
                def _una(match, repl=repl):
                    src = match.group(0)
                    if src[:1].isupper():
                        return repl[:1].upper() + repl[1:]
                    return repl
                text = pattern.sub(_una, text)
            return text

        for model in apps.get_models():
            # Los artículos del blog son texto entregado por el estudio. No se reescribe.
            if model._meta.label in ("blog.Post", "blog.Comment"):
                continue
            fields = [
                f for f in model._meta.concrete_fields
                if f.get_internal_type() in ("CharField", "TextField")
            ]
            if not fields:
                continue
            for obj in model.objects.all():
                changed = []
                for field in fields:
                    value = getattr(obj, field.name)
                    if not isinstance(value, str) or not re.search(r"negocio", value, re.I):
                        continue
                    nuevo = reemplazar(value)
                    if nuevo != value:
                        setattr(obj, field.name, nuevo)
                        changed.append(field.name)
                if changed:
                    obj.save(update_fields=changed)

    # ------------------------------------------------------------------
    def seed_settings(self):
        s = SiteSettings.load()
        if not s.about_text:
            s.about_text = (
                "<p><strong>Inicia Legal</strong> es un estudio jurídico especializado en asesoría legal "
                "preventiva para pymes y empresas en crecimiento. Creemos que las mejores decisiones "
                "legales se toman antes de que el problema comience.</p>"
                "<p>Por eso trabajamos con un modelo de <strong>respaldo jurídico permanente</strong>: "
                "asesoría continua y un equipo de abogados especializados en las áreas "
                "críticas de la operación empresarial: civil, societario, laboral, tributario y penal económico.</p>"
                "<p>Acompañamos a nuestros clientes antes de firmar, contratar, despedir o negociar, "
                "para que operen con seguridad, orden y tranquilidad durante todo el año.</p>"
            )
            s.save()
        if s.about_text and "civil y comercial, laboral, tributaria y penal económica" in s.about_text:
            s.about_text = s.about_text.replace(
                "civil y comercial, laboral, tributaria y penal económica",
                "civil, societario, laboral, tributario y penal económico",
            )
            s.save(update_fields=["about_text"])
        if s.about_text and "costo fijo" in s.about_text.lower():
            s.about_text = s.about_text.replace("asesoría continua, costo fijo y un equipo", "asesoría continua y un equipo")
            s.about_text = s.about_text.replace("asesoría continua, Costo fijo y un equipo", "asesoría continua y un equipo")
            s.save(update_fields=["about_text"])
        if s.about_text and "protección de datos y ciberseguridad, y propiedad industrial" in s.about_text:
            s.about_text = s.about_text.replace(
                "protección de datos y ciberseguridad, y propiedad industrial",
                "protección de datos, ciberseguridad, y propiedad industrial",
            )
            s.save(update_fields=["about_text"])
        # Copy del hero: se actualiza solo si aún tiene los textos de la primera versión (no pisa ediciones del admin)
        legacy_hero = {
            "hero_kicker": "Estudio jurídico para empresas y personas",
            "hero_title": "Respaldo jurídico permanente para tu empresa",
            "hero_subtitle": "Asesoría legal continua, prevención real y un equipo especializado para que tu empresa opere con seguridad, orden y tranquilidad.",
            "hero_secondary_text": "Conoce el Plan Legal Advance",
        }
        changed = False
        for field, old in legacy_hero.items():
            if getattr(s, field) == old:
                setattr(s, field, SiteSettings._meta.get_field(field).default)
                changed = True
        # Dirección: se completa solo si aún no hay una registrada
        if not s.address:
            s.address = SiteSettings._meta.get_field("address").default
            changed = True
        if s.city == "Santiago, Chile":
            s.city = SiteSettings._meta.get_field("city").default
            changed = True
        s.cta_title = "Solicite una reunión"
        s.cta_text = "La primera reunión no tiene costo."
        s.cta_button_text = "Solicite una reunión"
        if s.hero_primary_text in ("Agenda una asesoría", "Agendar asesoría"):
            s.hero_primary_text = "Solicite una reunión"
            changed = True
        if s.hero_secondary_text == "Conoce nuestros planes":
            s.hero_secondary_text = "Conozca nuestros planes"
            changed = True
        legacy_cookie_markers = ("atender tus solicitudes", "Puedes aceptar", "configurar tus preferencias")
        if s.cookie_consent_text and any(m in s.cookie_consent_text for m in legacy_cookie_markers):
            s.cookie_consent_text = SiteSettings._meta.get_field("cookie_consent_text").default
            changed = True
        legacy_footer = "Acompañamos tus decisiones"
        if s.footer_text and legacy_footer in s.footer_text:
            s.footer_text = SiteSettings._meta.get_field("footer_text").default
            changed = True
        s.about_kicker = "Nosotros"
        s.about_title = "Criterio jurídico para las decisiones de la empresa"
        s.about_text = (
            "<p>Inicia Legal es un estudio jurídico corporativo que asesora a empresas en crecimiento "
            "en las materias que definen su operación; derecho societario y contractual, laboral, tributario, "
            "penal económico y compliance, protección de datos, ciberseguridad, y propiedad industrial.</p>"
            "<p>Nuestra práctica se funda en un principio: las contingencias jurídicas de una empresa se resuelven "
            "con mayor eficacia antes de que se produzcan. Por ello, acompañamos a nuestros clientes de manera "
            "permanente en la celebración de sus contratos, la gestión de sus relaciones laborales, su estructuración "
            "societaria y su cumplimiento normativo.</p>"
            "<p>Cada asunto es conducido por abogados especializados en el área respectiva, con el rigor técnico "
            "de un gran estudio y una comprensión cercana de la empresa de cada cliente.</p>"
        )
        s.footer_text = (
            "Estudio jurídico corporativo. Asesoramos a empresas en derecho societario, laboral, "
            "tributario, penal económico y compliance."
        )
        s.cookie_consent_text = SiteSettings._meta.get_field("cookie_consent_text").default
        s.meta_description = (
            "Estudio jurídico corporativo en Las Condes. Asesoría a empresas en derecho societario, "
            "laboral, tributario, penal económico y compliance."
        )
        s.google_analytics_id = "G-RH0BM2DENP"
        s.youtube = "https://www.youtube.com/@IniciaLegal"
        s.linkedin = "https://www.linkedin.com/company/inicia-legal/"
        s.instagram = "https://www.instagram.com/inicialegal.cl/?hl=es"
        changed = True
        if changed:
            s.save()
        attach_image(s, "hero_image", "oficina-panoramica.jpg")
        attach_image(s, "about_image", "asesoria-manos.jpg")
        self.stdout.write("· Configuración del sitio")

    def seed_areas(self):
        # Seis grupos de la estrategia. Las once materias viven dentro del grupo;
        # no se publican como prácticas sueltas.
        data = [
            ("corporativo", "Derecho societario", "Corporativo", "bi-building", "societario.jpg",
             CORPORATIVO_SHORT, build_corporativo_html()),
            ("derecho-laboral", "Derecho laboral", "Laboral", "bi-people", "reunion-laboral.jpg",
             "Reglamento interno, jornada, auditoría laboral y juicios laborales.",
             "<p>Acompañamos a la empresa en el cumplimiento laboral y en la defensa de sus contingencias.</p>"
             '<h2 class="h3 mt-5 mb-4">Servicios laborales</h2><ul>'
             "<li>Reglamento interno con protocolo de la Ley N.º 21.643</li>"
             "<li>Adecuación de jornada a la Ley N.º 21.561</li>"
             "<li>Pactos de horas extraordinarias</li>"
             "<li>Auditoría laboral</li>"
             "<li>Juicios laborales</li></ul>"),
            ("derecho-tributario", "Derecho tributario", "Tributario", "bi-calculator", "informes-financieros.jpg",
             "Planificación, reestructuraciones y regularizaciones ante el Servicio de Impuestos Internos.",
             "<p>Orientamos las decisiones de la empresa cuando tienen efecto tributario y en su relación "
             "con el Servicio de Impuestos Internos.</p>"
             '<h2 class="h3 mt-5 mb-4">Servicios tributarios</h2><ul>'
             "<li>Planificación tributaria</li>"
             "<li>Reestructuraciones con efecto tributario</li>"
             "<li>Regularizaciones ante el Servicio de Impuestos Internos</li>"
             "<li>Regularización de rentas de fuente extranjera no declaradas en Chile (2025, 2024 y 2023, no prescritos)</li>"
             "<li>Defensa ante notificaciones, citaciones y fiscalizaciones del Servicio de Impuestos Internos</li>"
             "<li>Due diligence tributario</li></ul>"),
            ("derecho-penal-economico", "Derecho penal económico", "Penal económico y compliance", "bi-shield-lock", "justicia-lupa.jpg",
             "Modelos de prevención de delitos, programas de cumplimiento e investigaciones internas.",
             "<p>Prevenimos y analizamos la responsabilidad penal de la persona jurídica y de su administración.</p>"
             '<h2 class="h3 mt-5 mb-4">Servicios en penal económico y compliance</h2><ul>'
             "<li>Modelos de prevención conforme a las Leyes N.º 20.393 y N.º 21.595</li>"
             "<li>Programas de cumplimiento</li>"
             "<li>Investigaciones internas</li>"
             "<li>Canal de denuncias</li></ul>"),
            ("tecnologia-y-datos", None, "Tecnología y datos", "bi-laptop", "banner-blog.jpg",
             TECNOLOGIA_DATOS_SHORT, build_tecnologia_datos_html()),
            ("propiedad-industrial", None, "Propiedad industrial", "bi-award", "marca-registrada.jpg",
             "Registro y defensa de marcas y patentes.",
             "<p>Protegemos los signos distintivos de la empresa ante el Instituto Nacional de Propiedad Industrial "
             "y el Tribunal de Propiedad Industrial.</p>"
             '<h2 class="h3 mt-5 mb-4">Servicios en propiedad industrial</h2><ul>'
             "<li>Registro de marcas ante el Instituto Nacional de Propiedad Industrial</li>"
             "<li>Oposiciones</li>"
             "<li>Defensa y apelaciones ante el Tribunal de Propiedad Industrial</li></ul>"),
        ]
        areas = {}
        slugs = []
        for i, (slug, old_name, name, icon, image, short, desc) in enumerate(data):
            obj = PracticeArea.objects.filter(slug=slug).first()
            if obj is None and old_name:
                obj = PracticeArea.objects.filter(name=old_name).first()
            if obj is None:
                obj = PracticeArea(slug=slug)
            obj.name = name
            obj.slug = slug
            obj.icon = icon
            obj.short_description = short
            obj.description = desc
            obj.order = i
            obj.show_on_home = True
            obj.is_active = True
            obj.save()
            attach_image(obj, "image", image)
            areas[name] = obj
            slugs.append(slug)
        PracticeArea.objects.exclude(slug__in=slugs).update(is_active=False, show_on_home=False)
        self.stdout.write(f"· Grupos de práctica ({len(areas)})")
        return areas

    def seed_services(self, areas):
        # Servicios Corporativo: ver sync_corporativo / corporativo_content.py
        data = [
            ("Cumplimiento laboral", "bi-person-badge", "Laboral",
             "Contratos de trabajo, anexos, reglamento interno, desvinculaciones y respuesta a fiscalizaciones.", False),
            ("Protección de marca", "bi-award", "Propiedad industrial",
             "Registro y defensa de marcas comerciales ante INAPI para proteger la identidad de la empresa.", False),
            ("Orientación tributaria", "bi-calculator", "Tributario",
             "Asesoría legal en materias tributarias vinculadas a la operación y estructura de la empresa.", False),
            ("Regularización de rentas de fuente extranjera", "bi-globe", "Tributario",
             "Regularización ante el SII de rentas de fuente extranjera no declaradas en Chile durante 2025, 2024 y 2023, años no prescritos.", False),
            ("Defensa tributaria ante el SII", "bi-shield", "Tributario",
             "Defensa de la empresa ante notificaciones, citaciones y cualquier fiscalización del Servicio de Impuestos Internos.", False),
            ("Prevención de delitos económicos", "bi-shield-lock", "Penal económico y compliance",
             "Modelos de prevención y análisis de riesgos de responsabilidad penal empresarial.", False),
        ]
        included = {
            "Revisión de contratos": "Incluido en Plan Legal Pyme y Plan Legal Advance",
            "Confección de contratos": "Incluido en los planes anuales",
            "Asesoría legal continua": "Incluido en Plan Legal Pyme y Plan Legal Advance",
        }
        images = {"Protección de marca": "marca-boceto.jpg"}
        for i, (name, icon, area, short, featured) in enumerate(data):
            obj, _ = Service.objects.update_or_create(
                name=name,
                defaults={
                    "icon": icon, "area": areas.get(area), "short_description": short, "is_featured": featured, "order": 500 + i,
                    "description": f"<p>{short}</p><p>Solicite una reunión para recibir una propuesta acorde a la empresa.</p>",
                    "price_note": included.get(name, "Cotizar"),
                },
            )
            attach_image(obj, "image", images.get(name))
        self.stdout.write(f"· Servicios ({len(data)})")

    def seed_plan(self):
        shared_problem = (
            "Contratos firmados sin revisión, incumplimientos laborales, falta de protección de marca, conflictos "
            "con clientes o proveedores y consultas legales resueltas tarde pueden generar costos, multas, demandas "
            "y pérdida de tiempo directivo.\n\nEl riesgo no siempre se ve al inicio, pero aparece cuando la empresa ya está expuesta."
        )
        tagline = "Respaldo jurídico permanente para empresas que quieren operar con seguridad, orden y prevención legal."
        summary = (
            "Un servicio jurídico anual para que la empresa cuente con respaldo legal permanente, "
            "asesoría preventiva y acompañamiento estratégico en sus decisiones más importantes."
        )
        benefits = [
            ("Respaldo durante todo el año", "Evita la incertidumbre de contratar abogados por cada consulta o documento."),
            ("Prevención de riesgos", "Permite detectar y corregir problemas antes de que escalen."),
            ("Mejores decisiones empresariales", "Acceso a orientación legal antes de firmar, contratar, despedir o negociar."),
            ("Orden legal permanente", "Contratos, cumplimiento laboral, marca y documentos bajo revisión profesional."),
            ("Acompañamiento especializado", "Equipo jurídico disponible en las principales áreas críticas de la empresa."),
        ]
        team = ("bi-people", "Equipo jurídico especializado", "Acceso a un equipo en materias corporativas, laborales, tributarias, de penal económico y compliance, de datos y de propiedad industrial.")
        consults = ("bi-chat-dots", "Asesorías legales", "Consultas ordinarias durante la vigencia del plan.")
        audits = ("bi-clipboard-check", "Auditoría laboral", "2 auditorías anuales, una por semestre.")
        reviews = ("bi-file-earmark-text", "Revisión de contratos", "Hasta 3 contratos mensuales.")
        ejecutivo = ("bi-bank", "Cobranza judicial", "Cobranza judicial de facturas, cheques y pagarés.")
        specs = {
            "plan-legal-pyme": {
                "order": 0, "featured": False, "name": "Plan Legal Pyme", "price": 60, "brochure": "plan-legal-pyme.pdf",
                "features": [
                    team, consults,
                    ("bi-pencil-square", "Confección de contratos", "2 contratos anuales diseñados a la medida de la empresa."),
                    audits, reviews, ejecutivo,
                ],
            },
            "plan-legal-advance": {
                "order": 1, "featured": True, "name": "Plan Legal Advance", "price": 105, "brochure": "plan-legal-advance.pdf",
                "features": [
                    team, consults,
                    ("bi-pencil-square", "Confección de contratos", "4 contratos anuales diseñados a la medida de la empresa."),
                    audits, reviews, ejecutivo,
                    ("bi-person-workspace", "Juicio laboral", "Juicio ordinario o monitorio."),
                ],
            },
        }
        saved = {}
        for slug, spec in specs.items():
            plan, _ = Plan.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": spec["name"],
                    "tagline": tagline,
                    "summary": summary,
                    "problem_title": "Muchas Pymes toman decisiones legales cuando el problema ya comenzó.",
                    "problem_text": shared_problem,
                    "solution_title": f"{spec['name']} de Inicia Legal",
                    "solution_text": (
                        f"Con el {spec['name']}, la empresa deja de reaccionar frente a las contingencias jurídicas y comienza a "
                        "prevenirlos con apoyo profesional durante todo el año."
                    ),
                    "currency": "UF",
                    "price_annual": spec["price"],
                    "price_installment": None,
                    "installments": 12,
                    "price_suffix": "+ IVA",
                    "payment_modality": "En 12 cuotas",
                    "price_note": "Medios de pago: transferencia electrónica, tarjeta de débito o crédito.",
                    "discount_badge": "Hasta 15% de descuento en servicios adicionales",
                    "discount_text": (
                        f"Al contratar el {spec['name']}, la empresa accede a una tarifa preferente para servicios jurídicos "
                        "adicionales que no estén incluidos en el plan. Este beneficio aplica sobre honorarios profesionales "
                        "de Inicia Legal, previa evaluación y cotización del servicio requerido."
                    ),
                    "is_featured": spec["featured"],
                    "cta_text": "Solicite su plan",
                    "order": spec["order"],
                },
            )
            titles = []
            for i, (icon, title, text) in enumerate(spec["features"]):
                PlanFeature.objects.update_or_create(plan=plan, title=title, defaults={"icon": icon, "text": text, "order": i})
                titles.append(title)
            PlanFeature.objects.filter(plan=plan).exclude(title__in=titles).delete()
            benefit_titles = []
            for i, (title, text) in enumerate(benefits):
                PlanBenefit.objects.update_or_create(plan=plan, title=title, defaults={"text": text, "order": i})
                benefit_titles.append(title)
            PlanBenefit.objects.filter(plan=plan).exclude(title__in=benefit_titles).delete()
            attach_image(plan, "brochure", spec["brochure"])
            saved[slug] = plan
        self.stdout.write("· Plan Legal Pyme y Plan Legal Advance")
        return saved

    def seed_stats(self):
        # La estrategia 2026 retira estas cifras hasta contar con evidencia de trayectoria.
        # El 15% permanece en la ficha de los planes.
        Stat.objects.filter(
            label__in=[
                "Abogados especializados",
                "Socias fundadoras",
                "Áreas de práctica clave",
                "Meses de respaldo permanente",
                "Descuento en servicios adicionales",
            ]
        ).update(is_active=False)
        self.stdout.write("· Cifras de trayectoria retiradas")

    def seed_faqs(self, plans):
        FAQ.objects.filter(question="¿Atienden solo a empresas o también a personas?", plan=None).delete()
        general = [
            ("¿A quién asesora Inicia Legal?", "Inicia Legal asesora a empresas, a sus socios y a sus administradores. Los asuntos penales de personas naturales son atendidos por Abogadas Penalistas, firma relacionada especializada en defensa penal."),
            ("¿La primera reunión tiene costo?", "No. La reunión inicial no tiene costo y permite conocer la situación jurídica de la empresa."),
            ("¿Atienden de forma remota?", "Sí. El estudio trabaja de manera presencial y remota, con reuniones por videollamada y gestión documental digital."),
            ("¿Cómo puedo contactarlos?", "Puede escribir a través del formulario, del correo, del teléfono o de WhatsApp. Respondemos a la brevedad en horario hábil."),
        ]
        for i, (q, a) in enumerate(general):
            FAQ.objects.update_or_create(question=q, plan=None, defaults={"answer": a, "order": i})
        per_plan = {
            "plan-legal-pyme": (
                "Incluye equipo jurídico especializado, consultas ordinarias durante la vigencia, 2 contratos anuales a la medida, "
                "2 auditorías laborales al año, revisión de hasta 3 contratos mensuales y cobranza judicial de facturas, cheques y pagarés."
            ),
            "plan-legal-advance": (
                "Incluye equipo jurídico especializado, consultas ordinarias durante la vigencia, 4 contratos anuales a la medida, "
                "2 auditorías laborales al año, revisión de hasta 3 contratos mensuales, cobranza judicial de facturas, cheques y pagarés "
                "y juicio laboral ordinario o monitorio."
            ),
        }
        for slug, includes in per_plan.items():
            plan = plans[slug]
            rows = [
                (f"¿Qué incluye el {plan.name}?", includes),
                ("¿Cuál es la duración del plan?", "El plan tiene una vigencia anual y puede pagarse en hasta 12 cuotas."),
                ("¿Qué pasa si necesito un servicio que no está incluido?", "Como cliente del plan accede a una tarifa preferente de hasta 15% de descuento sobre honorarios profesionales de Inicia Legal, previa evaluación y cotización."),
                ("¿Cómo se activa el plan?", "Se confirma la modalidad de pago y se coordina la reunión inicial. Desde ese momento la empresa cuenta con respaldo jurídico permanente."),
            ]
            for i, (q, a) in enumerate(rows):
                FAQ.objects.update_or_create(question=q, plan=plan, defaults={"answer": a, "order": i})
        FAQ.objects.filter(answer__contains="accedes a una tarifa preferente").update(
            answer="Como cliente del plan accede a una tarifa preferente de hasta 15% de descuento sobre honorarios profesionales de Inicia Legal, previa evaluación y cotización."
        )
        self.stdout.write("· Preguntas frecuentes")

    def seed_team(self, areas):
        data = [
            ("angela-montiel", "Ángela María Montiel Báez", "Socia fundadora", "Abogada corporativa", "angela-montiel.jpg", "",
             ["Corporativo", "Tributario", "Tecnología y datos"],
             "<p><strong>Ángela María Montiel Báez</strong> es abogada corporativa y socia fundadora de Inicia Legal. "
             "Acompaña a empresas y pymes en la estructuración de sus relaciones contractuales, la prevención de "
             "conflictos y la toma de decisiones con respaldo jurídico.</p>"
             "<h3>Formación</h3><ul>"
             "<li>Abogada.</li>"
             "<li>Diplomado en Contratación Pública, Universidad de Chile (2023).</li>"
             "<li>Diplomado en Responsabilidad Civil, Universidad de Chile (2024).</li>"
             "<li>Diplomado en Tributación Corporativa, Universidad Andrés Bello (2026).</li>"
             "</ul>"
             "<h3>Áreas de ejercicio</h3><p>Derecho societario, contratación civil, contratación pública, responsabilidad civil y tributación corporativa.</p>"),
            ("natalia-acuna", "Natalia Acuña Illanes", "Socia fundadora", "Abogada penalista", "natalia-acuna.jpg", "natalia.acuna@inicialegal.cl",
             ["Penal económico y compliance"],
             "<p><strong>Natalia Acuña Illanes</strong> es abogada penalista y socia fundadora de Inicia Legal. "
             "Se especializa en la prevención y el análisis de riesgos asociados a delitos económicos y a la "
             "responsabilidad penal de las empresas, así como en materias de cumplimiento ambiental.</p>"
             "<h3>Formación</h3><ul>"
             "<li>Abogada.</li>"
             "<li>Diplomado en Derecho Penal Económico, Pontificia Universidad Católica de Chile (2021).</li>"
             "<li>Diplomado en Derecho Ambiental – Instrumentos de Gestión Ambiental, Universidad de Chile (2023).</li>"
             "</ul>"
             "<h3>Áreas de ejercicio</h3><p>Derecho penal económico, responsabilidad penal de personas jurídicas, compliance y derecho ambiental.</p>"),
            ("fadwa-saba", "Fadwa Saba", "Abogada", "Especialista en Derecho Penal", None, "",
             [],
             "<p><strong>Fadwa Saba</strong> es abogada especialista en Derecho Penal. "
             "Ejerció durante más de 10 años como Defensora Penal Pública en la Región Metropolitana. "
             "Se especializa en delitos violentos, Ley 20.000, Ley de armas, Ley de Tránsito, VIF y delitos contra las personas y propiedades.</p>"
             "<h3>Formación</h3><ul>"
             "<li>Abogada.</li>"
             "<li>Master en Derecho Penal y Ciencias Criminales, Universidad de Sevilla, España (2023).</li>"
             "<li>Master en Derecho Penal y Garantías Constitucionales, Universidad de Jaén, España (2018).</li>"
             "<li>Diplomado en Igualdad y no discriminación, Universidad de Buenos Aires, Argentina (2022).</li>"
             "<li>Diplomado en Análisis Criminal para la gestión de la seguridad, Universidad Alberto Hurtado (2022).</li>"
             "<li>Diplomado en Derecho Penal Económico, Universidad Católica de Chile (2021).</li>"
             "<li>Diplomado en Garantías Constitucionales, Universidad de Jaén, España (2019).</li>"
             "</ul>"
             "<h3>Áreas de ejercicio</h3><p>Delitos violentos, Ley 20.000, Ley de armas, Ley de Tránsito, VIF y delitos contra las personas y propiedades.</p>"),
            ("juan-gallardo", "Juan Gallardo Vera", "Abogado", "Especialista en Derecho Laboral", "juan-gallardo.jpg", "",
             ["Laboral"],
             "<p><strong>Juan Gallardo Vera</strong> es abogado especialista en Derecho Laboral.</p>"
             "<h3>Formación</h3><ul>"
             "<li>Abogado, Universidad Central de Chile.</li>"
             "<li>Administrador de Personal, Universidad de Santiago de Chile.</li>"
             "<li>Diplomado de Responsabilidad Social Empresarial, Universidad Alberto Hurtado (2010).</li>"
             "</ul>"
             "<h3>Áreas de ejercicio</h3><p>Derecho laboral.</p>"),
        ]
        for i, (slug, name, role, specialty, photo, email, area_names, bio) in enumerate(data):
            m, _ = TeamMember.objects.update_or_create(
                slug=slug, defaults={"name": name, "role": role, "specialty": specialty, "bio": bio, "email": email, "order": i, "show_on_home": True},
            )
            attach_image(m, "photo", photo)
            m.areas.set([areas[a] for a in area_names if a in areas])
        self.stdout.write(f"· Equipo ({len(data)})")

    def seed_hero(self):
        slides = [
            ("principal", "overlay", 0, "oficina-panoramica.jpg", "oficina-panoramica-m.jpg",
             "Estudio jurídico corporativo",
             "Rigor jurídico. *Visión de empresa.*",
             "Asesoría especializada en derecho societario, laboral, tributario, penal económico y compliance, protección de datos y propiedad industrial.",
             "Conozca nuestras áreas", "/#areas", "", ""),
            ("banners", "overlay", 1, "hero-publicaciones.jpg", None,
             "Publicaciones",
             "Lo que conviene saber *antes de firmar*",
             "Artículos prácticos sobre contratos, laboral, tributario, penal económico y propiedad industrial.",
             "Ver las publicaciones", "/blog/", "", ""),
            ("planes", "overlay", 2, "hero-respaldo.jpg", None,
             "Asesoría permanente",
             "Respaldo *anual*",
             "Planes de asesoría jurídica para empresas.",
             "Conozca nuestros planes", "/planes/", "", ""),
        ]
        keys = []
        for key, variant, order, image, mobile, kicker, title, subtitle, ptext, purl, stext, surl in slides:
            keys.append(key)
            slide, _ = HeroSlide.objects.update_or_create(
                key=key,
                defaults={
                    "variant": variant, "order": order, "is_active": True,
                    "kicker": kicker, "title": title, "subtitle": subtitle,
                    "primary_text": ptext, "primary_url": purl,
                    "secondary_text": stext, "secondary_url": surl,
                },
            )
            attach_image(slide, "image", image)
            attach_image(slide, "image_mobile", mobile)
        HeroSlide.objects.exclude(key__in=keys).update(is_active=False)
        self.stdout.write(f"· Carrusel del inicio ({len(slides)})")

    def seed_testimonials(self):
        # Se crean desactivados: reemplazar por testimonios reales antes de activar.
        data = [
            ("Nombre Cliente", "Empresa de ejemplo SpA", "Gerente General", "Desde que contratamos el plan, cada contrato pasa por revisión antes de firmar. Dejamos de apagar incendios."),
            ("Nombre Cliente", "Comercial Ejemplo Ltda.", "Socia", "Tener un equipo legal disponible nos permitió ordenar la parte laboral y tributaria sin sorpresas."),
        ]
        if not Testimonial.objects.exists():
            for i, (name, company, position, quote) in enumerate(data):
                Testimonial.objects.create(client_name=name, company=company, position=position, quote=quote, is_active=False, order=i)
        for t in Testimonial.objects.filter(quote__icontains="costo fijo"):
            t.quote = t.quote.replace(" a costo fijo", "").replace("a costo fijo ", "")
            t.save(update_fields=["quote"])
        self.stdout.write("· Testimonios de ejemplo (desactivados)")

    def seed_pages(self):
        pages = [
            ("Política de privacidad", "privacidad",
             "<p><em>Fecha de última actualización: 19 de agosto de 2025.</em></p>"
             "<h2>I. Introducción</h2>"
             "<p>En Inicia Legal SpA (en adelante, “Inicia Legal”, “nosotros” o “nuestro”), valoramos y respetamos la privacidad de todas las personas que nos confían sus datos personales.</p>"
             "<p>El presente documento explica cómo recolectamos, utilizamos, almacenamos, compartimos y protegemos los datos personales de nuestros clientes, prospectos, usuarios del sitio web y demás personas naturales cuyos datos tratamos.</p>"
             "<p>Esta política se dicta en conformidad con la Ley N.° 21.719 sobre Protección y Tratamiento de los Datos Personales (vigente a partir del 1.° de diciembre de 2026) y, de manera complementaria, con los principios y buenas prácticas del Reglamento General de Protección de Datos (GDPR) de la Unión Europea.</p>"
             "<p>El acceso y uso del sitio web de Inicia Legal implica el conocimiento y aceptación de la presente Política de Privacidad.</p>"
             "<h2>II. Responsable del tratamiento</h2>"
             "<p><strong>Responsable:</strong> Inicia Legal 360 - Estudio Jurídico SpA, RUT: 78.206.685-4.</p>"
             "<p><strong>Dirección:</strong> Los Militares N.° 5620, oficina N.° 905, comuna de Las Condes.</p>"
             "<p><strong>Encargado de Protección de Datos (DPD):</strong> Angela Montiel Báez.</p>"
             "<p><strong>Contacto para el ejercicio de derechos:</strong> <a href=\"mailto:angelamontiel@inicialegal.cl\">angelamontiel@inicialegal.cl</a>.</p>"
             "<h2>III. Principios rectores del tratamiento</h2>"
             "<p>En cumplimiento de la Ley N.° 21.719, el tratamiento de datos personales en Inicia Legal se rige por los siguientes principios:</p>"
             "<ol>"
             "<li><strong>Licitud y lealtad:</strong> solo tratamos datos de manera lícita y justa.</li>"
             "<li><strong>Finalidad:</strong> los datos se recolectan con fines específicos, explícitos y legítimos.</li>"
             "<li><strong>Proporcionalidad:</strong> tratamos solo los datos adecuados, pertinentes y necesarios.</li>"
             "<li><strong>Calidad:</strong> los datos deben ser exactos, completos y actualizados.</li>"
             "<li><strong>Seguridad:</strong> aplicamos medidas técnicas y organizativas apropiadas para proteger los datos.</li>"
             "<li><strong>Responsabilidad proactiva (accountability):</strong> Inicia Legal es responsable de demostrar el cumplimiento de esta política y de la ley.</li>"
             "<li><strong>Transparencia e información:</strong> informamos claramente sobre el tratamiento de los datos y mantenemos esta política permanentemente accesible.</li>"
             "<li><strong>Confidencialidad:</strong> todos quienes acceden a datos personales deben guardar secreto incluso después de terminada su relación con Inicia Legal.</li>"
             "</ol>"
             "<h2>IV. Definiciones</h2>"
             "<p>Para efectos de esta política, se aplicarán las siguientes definiciones, en concordancia con la Ley N.° 21.719:</p>"
             "<ol>"
             "<li><strong>Dato personal:</strong> cualquier información vinculada o referida a una persona natural identificada o identificable (por ejemplo: nombre, correo, RUT, dirección IP).</li>"
             "<li><strong>Dato personal sensible:</strong> información que revela aspectos íntimos de la persona, tales como salud, biometría, orientación sexual, creencias religiosas, convicciones políticas, entre otros.</li>"
             "<li><strong>Tratamiento de datos personales:</strong> cualquier operación realizada sobre datos personales, como la recolección, almacenamiento, comunicación, análisis o supresión.</li>"
             "<li><strong>Responsable de datos:</strong> persona natural o jurídica que decide sobre los fines y medios del tratamiento de datos. En este caso, Inicia Legal SpA.</li>"
             "<li><strong>Encargado de datos:</strong> persona o entidad que trata datos personales por cuenta del responsable. Por ejemplo: proveedores de hosting, correo electrónico o analítica.</li>"
             "<li><strong>Consentimiento:</strong> manifestación libre, específica, informada e inequívoca por la cual el titular acepta el tratamiento de sus datos.</li>"
             "<li><strong>Titular de datos:</strong> persona natural a quien pertenecen los datos personales.</li>"
             "</ol>"
             "<h2>V. Datos que recolectamos</h2>"
             "<p>Inicia Legal podrá recolectar y tratar las siguientes categorías de datos personales:</p>"
             "<ol>"
             "<li><strong>Datos de identificación y contacto:</strong> nombre, apellidos, correo electrónico, número de teléfono.</li>"
             "<li><strong>Datos de navegación:</strong> dirección IP, cookies, historial de navegación, identificadores en línea.</li>"
             "<li><strong>Información asociada a solicitudes o casos legales:</strong> antecedentes entregados voluntariamente por clientes o prospectos.</li>"
             "<li><strong>Datos de clientes, prospectos, socios y directores de personas jurídicas:</strong> obtenidos de fuentes públicas y privadas conforme a la ley.</li>"
             "<li><strong>Datos derivados de cookies y herramientas de analítica y marketing digital.</strong></li>"
             "</ol>"
             "<h2>VI. Finalidades del tratamiento</h2>"
             "<p>Los datos personales serán utilizados para los siguientes fines: (i) contacto directo con clientes y prospectos; (ii) envío de newsletters y comunicaciones comerciales; (iii) administración de cuentas y gestión contractual; (iv) contratación y ejecución de servicios legales y asesorías; (v) análisis estadístico del uso de nuestro sitio web; (vi) actividades de marketing digital y remarketing a través de herramientas como Google Ads y Google Analytics.</p>"
             "<p>En ningún caso utilizaremos los datos personales para fines incompatibles o distintos a los aquí informados.</p>"
             "<h2>VII. Bases de licitud</h2>"
             "<p>El tratamiento de datos se efectuará bajo alguna de las siguientes bases de legitimidad: (i) consentimiento del titular; (ii) ejecución de un contrato o medidas precontractuales solicitadas por el titular; (iii) cumplimiento de una obligación legal; (iv) interés legítimo de Inicia Legal, siempre que no prevalezcan los derechos del titular (por ejemplo, marketing directo).</p>"
             "<h2>VIII. Comunicación y transferencias</h2>"
             "<p>Los datos podrán ser comunicados a:</p>"
             "<ol>"
             "<li>Proveedores de servicios tecnológicos (hosting, correo electrónico, software de gestión, marketing digital).</li>"
             "<li>Google Ads, Google Analytics y otros prestadores de servicios situados en Chile y en el extranjero.</li>"
             "</ol>"
             "<p>En caso de transferencias internacionales, Inicia Legal se asegurará de que existan niveles adecuados de protección o cláusulas contractuales apropiadas, conforme a la Ley N.° 21.719 y estándares internacionales.</p>"
             "<p>Los proveedores o encargados de datos deberán eliminar o devolver la información al término de la relación contractual, y no podrán tratarla para fines distintos de los instruidos por Inicia Legal.</p>"
             "<h2>IX. Conservación de los datos</h2>"
             "<p>Los datos personales serán conservados solo por el tiempo necesario para cumplir con las finalidades informadas o mientras exista una relación contractual o precontractual con el titular.</p>"
             "<p>Posteriormente, los datos serán eliminados o anonimizados, salvo obligación legal de conservación.</p>"
             "<h2>X. Derechos de los titulares</h2>"
             "<p>En virtud de la Ley N.° 21.719 sobre Protección de Datos Personales, toda persona natural cuyos datos tratamos (el “titular”) tiene una serie de derechos fundamentales que le permiten mantener el control sobre su información personal.</p>"
             "<p>Estos derechos son irrenunciables, intransferibles y gratuitos, y pueden ejercerse en cualquier momento frente a Inicia Legal como responsable de los datos.</p>"
             "<h3>1. Derecho de acceso</h3>"
             "<p>Permite conocer si Inicia Legal trata o no sus datos personales y, en caso afirmativo, acceder a: (i) los datos específicos que tratamos sobre él; (ii) su origen; (iii) la finalidad del tratamiento; (iv) los destinatarios a los que se han comunicado o se prevé comunicar; (v) el plazo de conservación; (vi) la base legal del tratamiento.</p>"
             "<h3>2. Derecho de rectificación</h3>"
             "<p>Permite solicitar la modificación, corrección o actualización de los datos personales cuando sean inexactos, incompletos o desactualizados.</p>"
             "<p>Los cambios deberán comunicarse a terceros a quienes se hubieran entregado los datos originalmente.</p>"
             "<h3>3. Derecho de supresión (también denominado “derecho de cancelación”)</h3>"
             "<p>Faculta a solicitar la eliminación de los datos personales en los siguientes casos:</p>"
             "<ol>"
             "<li>Ya no sean necesarios para la finalidad para la que fueron recolectados.</li>"
             "<li>El titular retire su consentimiento y no exista otra base legal para el tratamiento.</li>"
             "<li>Los datos hayan sido tratados de manera ilícita.</li>"
             "<li>Los datos hayan caducado o deban eliminarse para cumplir una obligación legal o resolución judicial.</li>"
             "<li>El titular se haya opuesto válidamente al tratamiento.</li>"
             "</ol>"
             "<h3>4. Derecho de oposición</h3>"
             "<p>Permite oponerse a que los datos sean tratados en dos situaciones principales: (i) cuando la base legal del tratamiento sea el interés legítimo del responsable; (ii) cuando los datos se utilicen para marketing directo, incluida la elaboración de perfiles.</p>"
             "<p>Ejercido este derecho, Inicia Legal deberá dejar de tratar los datos salvo que existan motivos legítimos imperiosos que prevalezcan sobre los derechos del titular.</p>"
             "<h3>5. Derecho de portabilidad</h3>"
             "<p>Permite solicitar y recibir los datos personales en un formato electrónico estructurado, genérico y de uso común, de modo que pueda: (i) guardarlos para su uso personal; (ii) transferirlos a otro responsable de datos; (iii) solicitar, cuando sea técnicamente posible, que la transferencia se realice directamente entre responsables.</p>"
             "<p>Aplica cuando el tratamiento se base en consentimiento o contrato y se realice por medios automatizados.</p>"
             "<h3>6. Derecho de bloqueo temporal</h3>"
             "<p>Faculta a solicitar la suspensión temporal de cualquier tratamiento de sus datos personales mientras se resuelve una solicitud de acceso, rectificación, supresión u oposición.</p>"
             "<p>Durante el bloqueo, los datos podrán seguir almacenados, pero no podrán ser tratados hasta que se adopte una decisión definitiva.</p>"
             "<h3>Procedimiento</h3>"
             "<ol>"
             "<li>Enviar la solicitud, de forma gratuita, al correo <a href=\"mailto:angelamontiel@inicialegal.cl\">angelamontiel@inicialegal.cl</a>.</li>"
             "<li>Inicia Legal responderá en un plazo máximo de 30 días corridos, prorrogables por otros 30 en casos justificados.</li>"
             "<li>Si no recibe respuesta, el titular podrá reclamar ante la Agencia de Protección de Datos Personales.</li>"
             "</ol>"
             "<h2>XI. Seguridad de la información</h2>"
             "<p>Inicia Legal implementa medidas técnicas, administrativas y organizativas apropiadas para garantizar la confidencialidad, integridad, disponibilidad y resiliencia de los datos, incluyendo cifrado, seudonimización, copias de seguridad y controles de acceso.</p>"
             "<p>En caso de una vulneración de seguridad que pueda afectar derechos de los titulares, Inicia Legal notificará oportunamente a la Agencia de Protección de Datos Personales y, cuando corresponda, a los titulares afectados, indicando la naturaleza de la vulneración, sus consecuencias y las medidas adoptadas.</p>"
             "<h2>XII. Uso de cookies</h2>"
             "<p>Nuestro sitio utiliza cookies propias y de terceros para:</p>"
             "<ol>"
             "<li><strong>Cookies necesarias:</strong> habilitar el funcionamiento básico del sitio.</li>"
             "<li><strong>Cookies analíticas:</strong> medir y mejorar el rendimiento del sitio mediante Google Analytics.</li>"
             "<li><strong>Cookies de marketing:</strong> personalizar publicidad y campañas a través de Google Ads.</li>"
             "</ol>"
             "<p>El usuario podrá aceptar, rechazar o configurar el uso de cookies no esenciales desde el aviso habilitado en el sitio web. El detalle está en la <a href=\"/p/politica-de-cookies/\">Política de Cookies</a>.</p>"
             "<h2>XIII. Auditorías y modificaciones</h2>"
             "<p>Inicia Legal realizará auditorías internas periódicas para verificar el cumplimiento de esta política.</p>"
             "<p>Asimismo, podrá modificarla para ajustarla a cambios legales, tecnológicos o en la prestación de servicios. La nueva versión será publicada en este sitio web, indicando su fecha de vigencia.</p>"),
            ("Política de cookies", "politica-de-cookies",
             "<p>Este sitio utiliza cookies y tecnologías similares. Una cookie es un pequeño archivo que se guarda en tu "
             "dispositivo cuando visitas un sitio web y que permite reconocer tu navegador en visitas posteriores.</p>"
             "<h3>Categorías que utilizamos</h3>"
             "<ul>"
             "<li><strong>Necesarias (siempre activas):</strong> permiten el funcionamiento básico y seguro del sitio, como la "
             "protección de formularios (CSRF), la sesión del administrador y recordar tu elección de consentimiento.</li>"
             "<li><strong>Analíticas (requieren tu consentimiento):</strong> nos ayudan a medir visitas y entender cómo se usa el "
             "sitio para mejorarlo. Solo se activan si las aceptas.</li>"
             "<li><strong>Marketing (requieren tu consentimiento):</strong> personalizan publicidad y campañas, por ejemplo a través de Google Ads. Solo se activan si las aceptas.</li>"
             "</ul>"
             "<h3>Tu consentimiento</h3><p>Al ingresar al sitio te preguntamos qué categorías autorizas. Puedes aceptarlas, "
             "rechazarlas o configurarlas por separado. Hasta que no otorgues tu consentimiento no se instala ninguna cookie "
             "que no sea estrictamente necesaria. Tu elección se guarda por 180 días y puedes cambiarla en cualquier momento "
             "desde el enlace <strong>«Configurar cookies»</strong> al pie de página.</p>"
             "<h3>Cómo eliminar cookies</h3><p>También puedes borrar o bloquear cookies desde la configuración de tu navegador. "
             "Ten en cuenta que bloquear las cookies necesarias puede afectar el funcionamiento del sitio.</p>"
             "<h3>Marco normativo</h3><p>Tratamos la información obtenida mediante cookies de acuerdo con la Ley N.° 19.628 y la "
             "Ley N.° 21.719 sobre Protección de Datos Personales. Para más información revisa nuestra "
             "<a href=\"/p/privacidad/\">Política de Privacidad</a> o escríbenos a contacto@inicialegal.cl.</p>"),
            ("Términos y condiciones", "terminos-y-condiciones",
             "<p>El contenido de este sitio web tiene fines informativos y no constituye asesoría legal. La información "
             "publicada en el blog corresponde a orientación general y puede no aplicarse a tu situación particular.</p>"
             "<p>La relación profesional con Inicia Legal se inicia únicamente con la aceptación expresa de una propuesta "
             "de servicios. Los valores publicados en el sitio son referenciales y pueden variar según la evaluación de cada caso.</p>"),
        ]
        for i, (title, slug, content) in enumerate(pages):
            Page.objects.update_or_create(slug=slug, defaults={"title": title, "content": content, "order": i})
        self.stdout.write("· Páginas legales")

    def seed_blog(self, areas):
        from apps.core.blog_articles import ARTICLES

        colors = {
            "Societario": "#1F2E3A",
            "Protección de datos": "#4A6B7C",
            "Marcas": "#B5924C",
            "Tributario": "#7C6A46",
        }
        cats = {}
        for i, (name, color) in enumerate(colors.items()):
            cats[name], _ = Category.objects.update_or_create(name=name, defaults={"color": color, "order": i})

        titles = []
        for article in ARTICLES:
            titles.append(article["title"])
            published = timezone.make_aware(datetime.fromisoformat(article["published"]))
            post, _ = Post.objects.update_or_create(
                title=article["title"],
                defaults={
                    "category": cats[article["category"]],
                    "content": article["content"],
                    "excerpt": "",
                    "status": Post.PUBLISHED,
                    "is_featured": article["featured"],
                    "published_at": published,
                    "author_display": article["author"],
                },
            )
            post.tags.clear()
            area = article.get("area")
            post.areas.set([areas[area]] if area and area in areas else [])
            attach_image(post, "cover_image", article.get("cover"))

        Post.objects.exclude(title__in=titles).delete()
        Category.objects.filter(posts__isnull=True).delete()
        Tag.objects.filter(posts__isnull=True).delete()
        self.stdout.write(f"· Artículos del blog ({len(titles)})")

    def seed_admin(self):
        from django.conf import settings

        if not settings.DEBUG:
            self.stdout.write(self.style.WARNING("· En producción no se crea el usuario de desarrollo."))
            return
        User = get_user_model()
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write("· Ya existe un superusuario; no se creó otro.")
            return
        User.objects.create_superuser("admin", "contacto@inicialegal.cl", "admin1234", first_name="Inicia", last_name="Legal")
        self.stdout.write(self.style.WARNING("· Superusuario creado: admin / admin1234  (¡cámbialo en producción!)"))
