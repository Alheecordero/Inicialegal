import re
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field


class TimeStamped(models.Model):
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        abstract = True


class Publishable(TimeStamped):
    is_active = models.BooleanField("activo", default=True)
    order = models.PositiveIntegerField("orden", default=0)

    class Meta:
        abstract = True
        ordering = ["order", "id"]


def unique_slugify(instance, value, slug_field="slug"):
    """Genera un slug único para la instancia."""
    base = slugify(value)[:180] or "item"
    slug = base
    model = instance.__class__
    n = 2
    while model.objects.filter(**{slug_field: slug}).exclude(pk=instance.pk).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


# --------------------------------------------------------------------------
# Configuración global del sitio (singleton)
# --------------------------------------------------------------------------
class SiteSettings(models.Model):
    site_name = models.CharField("nombre del sitio", max_length=100, default="Inicia Legal")
    tagline = models.CharField(
        "eslogan", max_length=200, blank=True,
        default="Respaldo legal permanente para empresas que quieren operar con seguridad.",
    )
    logo = models.ImageField("logo", upload_to="site/", blank=True, help_text="Si se deja vacío se usa el logo por defecto.")
    logo_white = models.ImageField("logo blanco (pie de página)", upload_to="site/", blank=True)
    favicon = models.ImageField("favicon", upload_to="site/", blank=True)

    # Contacto
    email = models.EmailField("email de contacto", default="contacto@inicialegal.cl")
    phone = models.CharField("teléfono", max_length=30, default="+56 9 8752 9783")
    whatsapp = models.CharField(
        "WhatsApp", max_length=20, default="56987529783",
        help_text="Solo números con código de país, ej: 56987529783",
    )
    whatsapp_message = models.CharField(
        "mensaje inicial WhatsApp", max_length=200,
        default="Hola, me gustaría recibir más información sobre los servicios de Inicia Legal.",
    )
    address = models.CharField("dirección", max_length=200, blank=True, default="Los Militares N°5620, oficina N°905")
    city = models.CharField("ciudad", max_length=100, blank=True, default="Las Condes, Santiago")
    schedule = models.CharField("horario de atención", max_length=120, blank=True, default="Lunes a viernes, 9:00 a 18:00 hrs.")
    map_embed_url = models.URLField("URL de mapa (Google Maps embed)", blank=True)

    # Redes sociales
    instagram = models.URLField("Instagram", blank=True)
    linkedin = models.URLField("LinkedIn", blank=True)
    facebook = models.URLField("Facebook", blank=True)
    tiktok = models.URLField("TikTok", blank=True)
    youtube = models.URLField("YouTube", blank=True)

    # Hero
    hero_kicker = models.CharField("texto superior del hero", max_length=120, blank=True, default="Su empresa, con respaldo legal")
    hero_title = models.CharField(
        "título del hero", max_length=200, default="Soluciones legales para empresas que *quieren crecer*",
        help_text="Encierra entre asteriscos la parte que quieres destacar en dorado. Ej: Soluciones legales para empresas que *quieren crecer*",
    )
    hero_subtitle = models.TextField(
        "subtítulo del hero", blank=True,
        default="Acompañamos a emprendedores, e-commerce, startups y pymes en cada etapa de su empresa, con asesoría estratégica, clara y orientada a resultados.",
    )
    hero_image = models.ImageField("imagen del hero", upload_to="site/", blank=True, help_text="Horizontal, idealmente 2560×1080 px o mayor.")
    hero_image_mobile = models.ImageField("imagen del hero (móvil)", upload_to="site/", blank=True, help_text="Opcional. Vertical o cuadrada (ej. 1200×1400 px). Si se deja vacía se usa la imagen principal.")
    hero_primary_text = models.CharField("botón principal (texto)", max_length=60, default="Solicite una reunión")
    hero_primary_url = models.CharField("botón principal (URL)", max_length=200, default="/contacto/")
    hero_secondary_text = models.CharField("botón secundario (texto)", max_length=60, blank=True, default="Conozca nuestros planes")
    hero_secondary_url = models.CharField("botón secundario (URL)", max_length=200, blank=True, default="/planes/")

    # Sección "Nosotros" en el home
    about_kicker = models.CharField("nosotros · texto superior", max_length=120, blank=True, default="Quiénes somos")
    about_title = models.CharField("nosotros · título", max_length=200, blank=True, default="Un equipo jurídico que previene antes de corregir")
    about_text = CKEditor5Field("nosotros · texto", blank=True, config_name="default")
    about_image = models.ImageField("nosotros · imagen", upload_to="site/", blank=True)

    # Llamado a la acción final
    cta_title = models.CharField("CTA · título", max_length=200, blank=True, default="¿Su empresa está tomando decisiones legales a tiempo?")
    cta_text = models.TextField("CTA · texto", blank=True, default="Conversemos. La primera reunión no tiene costo.")
    cta_button_text = models.CharField("CTA · botón", max_length=60, blank=True, default="Solicite una reunión")
    cta_button_url = models.CharField("CTA · URL", max_length=200, blank=True, default="/contacto/")

    # SEO / otros
    meta_description = models.CharField("meta descripción por defecto", max_length=160, blank=True, default="Inicia Legal: asesoría legal preventiva para pymes y empresas en Chile. Plan Legal Advance, contratos, laboral, tributario y penal económico.")
    meta_keywords = models.CharField("palabras clave", max_length=255, blank=True, default="abogados, asesoría legal empresas, plan legal, pymes, Chile")
    google_analytics_id = models.CharField("Google Analytics ID", max_length=30, blank=True, help_text="Ej: G-XXXXXXXXXX")
    footer_text = models.TextField("texto del pie de página", blank=True, default="Estudio jurídico corporativo. Asesoramos a empresas en derecho societario, laboral, tributario, penal económico y compliance.")
    announcement = models.CharField("barra de anuncio", max_length=200, blank=True, help_text="Texto opcional que se muestra sobre el menú. Dejar vacío para ocultar.")
    announcement_url = models.CharField("URL del anuncio", max_length=200, blank=True)
    monogram = models.CharField("monograma decorativo", max_length=4, blank=True, default="IL", help_text="Letras gigantes que se muestran como marca de agua en el pie de página y la banda de contacto. Dejar vacío para ocultar.")

    # Consentimiento de cookies (Ley N.° 21.719)
    cookie_consent_enabled = models.BooleanField("mostrar aviso de cookies", default=True)
    cookie_consent_title = models.CharField("título del aviso", max_length=120, blank=True, default="Gestionar consentimiento")
    cookie_consent_text = models.TextField(
        "texto del aviso", blank=True,
        default=(
            "Este sitio web utiliza cookies y otras tecnologías, y trata los datos personales que nos proporcionas para "
            "ofrecer una mejor experiencia, atender sus solicitudes y cumplir las finalidades descritas en nuestra Política "
            "de Privacidad, de conformidad con la Ley N.° 21.719 sobre Protección de Datos Personales. Puede aceptar, "
            "rechazar o configurar sus preferencias en cualquier momento."
        ),
    )
    cookie_policy_url = models.CharField("URL de la política de cookies", max_length=200, blank=True, default="/p/politica-de-cookies/")
    privacy_policy_url = models.CharField("URL de la política de privacidad", max_length=200, blank=True, default="/p/privacidad/")

    class Meta:
        verbose_name = "configuración del sitio"
        verbose_name_plural = "configuración del sitio"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def whatsapp_link(self):
        from urllib.parse import quote
        return f"https://wa.me/{self.whatsapp}?text={quote(self.whatsapp_message)}"

    @property
    def social_links(self):
        items = [
            ("instagram", "Instagram", "bi-instagram", self.instagram),
            ("linkedin", "LinkedIn", "bi-linkedin", self.linkedin),
            ("facebook", "Facebook", "bi-facebook", self.facebook),
            ("tiktok", "TikTok", "bi-tiktok", self.tiktok),
            ("youtube", "YouTube", "bi-youtube", self.youtube),
        ]
        return [i for i in items if i[3]]


class HeroSlide(Publishable):
    """Diapositiva del carrusel de la portada. Si hay al menos una activa, reemplaza el hero único."""

    VARIANTS = [
        ("overlay", "Texto sobre la imagen"),
        ("art", "La imagen ya trae el mensaje"),
        ("plan", "Panel del plan"),
    ]
    key = models.SlugField("clave", unique=True)
    variant = models.CharField("estilo", max_length=20, choices=VARIANTS, default="overlay")
    kicker = models.CharField("texto superior", max_length=120, blank=True)
    title = models.CharField(
        "título", max_length=200, blank=True,
        help_text="Encierra entre asteriscos la parte que quieres destacar en dorado.",
    )
    subtitle = models.TextField("subtítulo", blank=True)
    image = models.ImageField("imagen", upload_to="site/hero/", blank=True, help_text="Horizontal, idealmente 2560×1080 px o mayor.")
    image_mobile = models.ImageField("imagen (móvil)", upload_to="site/hero/", blank=True, help_text="Opcional. Cuadrada o vertical. Si se deja vacía se usa la imagen principal.")
    primary_text = models.CharField("botón principal", max_length=60, blank=True)
    primary_url = models.CharField("URL principal", max_length=200, blank=True)
    secondary_text = models.CharField("botón secundario", max_length=60, blank=True)
    secondary_url = models.CharField("URL secundaria", max_length=200, blank=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "diapositiva del inicio"
        verbose_name_plural = "carrusel del inicio"

    def __str__(self):
        return self.title or self.key


# --------------------------------------------------------------------------
# Áreas de práctica / especialidades
# --------------------------------------------------------------------------
class PracticeArea(Publishable):
    name = models.CharField("nombre", max_length=120)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField("ícono (Bootstrap Icons)", max_length=60, default="bi-briefcase", help_text="Ej: bi-briefcase, bi-people, bi-bank. Ver icons.getbootstrap.com")
    short_description = models.CharField("descripción corta", max_length=255)
    description = CKEditor5Field("descripción completa", blank=True, config_name="default")
    image = models.ImageField("imagen", upload_to="areas/", blank=True)
    show_on_home = models.BooleanField("mostrar en inicio", default=True)

    class Meta(Publishable.Meta):
        verbose_name = "área de práctica"
        verbose_name_plural = "áreas de práctica"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("core:area_detail", args=[self.slug])


# --------------------------------------------------------------------------
# Servicios
# --------------------------------------------------------------------------
class Service(Publishable):
    name = models.CharField("nombre", max_length=120)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField("ícono (Bootstrap Icons)", max_length=60, default="bi-file-earmark-text")
    short_description = models.CharField("descripción corta", max_length=255)
    description = CKEditor5Field("descripción completa", blank=True, config_name="default")
    image = models.ImageField("imagen", upload_to="servicios/", blank=True)
    area = models.ForeignKey(PracticeArea, verbose_name="área relacionada", on_delete=models.SET_NULL, null=True, blank=True, related_name="services")
    is_featured = models.BooleanField("destacado en inicio", default=True)
    price_note = models.CharField("nota de precio", max_length=120, blank=True, help_text="Ej: Desde $150.000 + IVA, o 'Cotizar'.")

    class Meta(Publishable.Meta):
        verbose_name = "servicio"
        verbose_name_plural = "servicios"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("core:service_detail", args=[self.slug])


# --------------------------------------------------------------------------
# Planes (ej: Plan Legal Advance)
# --------------------------------------------------------------------------
class Plan(Publishable):
    name = models.CharField("nombre", max_length=120)
    slug = models.SlugField(unique=True, blank=True)
    tagline = models.CharField("bajada", max_length=200, blank=True)
    summary = models.TextField("resumen", blank=True)
    description = CKEditor5Field("descripción completa", blank=True, config_name="default")
    problem_title = models.CharField("sección problema · título", max_length=200, blank=True)
    problem_text = models.TextField("sección problema · texto", blank=True)
    solution_title = models.CharField("sección solución · título", max_length=200, blank=True)
    solution_text = models.TextField("sección solución · texto", blank=True)
    image = models.ImageField("imagen", upload_to="planes/", blank=True)

    currency = models.CharField("moneda", max_length=10, default="CLP")
    price_annual = models.DecimalField("valor anual", max_digits=12, decimal_places=0, null=True, blank=True)
    price_installment = models.DecimalField("valor cuota", max_digits=12, decimal_places=0, null=True, blank=True)
    installments = models.PositiveSmallIntegerField("número de cuotas", default=12)
    price_suffix = models.CharField("sufijo de precio", max_length=30, default="+ IVA")
    price_note = models.CharField("nota de precio", max_length=200, blank=True, default="Medios de pago: transferencia electrónica, tarjeta de débito o crédito.")
    payment_modality = models.CharField("modalidad", max_length=120, blank=True, default="Sin pago inicial")
    discount_badge = models.CharField("beneficio destacado", max_length=120, blank=True, default="Hasta 40% de descuento en servicios adicionales")
    discount_text = models.TextField("beneficio · texto", blank=True)

    is_featured = models.BooleanField("plan destacado", default=False)
    cta_text = models.CharField("texto del botón", max_length=60, default="Quiero este plan")
    brochure = models.FileField("brochure PDF", upload_to="planes/", blank=True)

    class Meta(Publishable.Meta):
        verbose_name = "plan"
        verbose_name_plural = "planes"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("core:plan_detail", args=[self.slug])

    @property
    def installment_amount(self):
        if self.price_annual is None or not self.installments:
            return None
        return (self.price_annual / self.installments).quantize(Decimal("0.01"))


class PlanFeature(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="features")
    icon = models.CharField("ícono", max_length=60, default="bi-check2-circle")
    title = models.CharField("título", max_length=120)
    text = models.CharField("detalle", max_length=255, blank=True)
    order = models.PositiveIntegerField("orden", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "servicio incluido"
        verbose_name_plural = "servicios incluidos"

    def __str__(self):
        return self.title


class PlanBenefit(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="benefits")
    title = models.CharField("título", max_length=120)
    text = models.CharField("detalle", max_length=255, blank=True)
    order = models.PositiveIntegerField("orden", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "beneficio"
        verbose_name_plural = "beneficios"

    def __str__(self):
        return self.title


# --------------------------------------------------------------------------
# Equipo
# --------------------------------------------------------------------------
class TeamMember(Publishable):
    name = models.CharField("nombre", max_length=120)
    slug = models.SlugField(unique=True, blank=True)
    role = models.CharField("cargo", max_length=120, default="Abogado/a")
    specialty = models.CharField("especialidad", max_length=160, blank=True)
    areas = models.ManyToManyField(PracticeArea, verbose_name="áreas", blank=True, related_name="members")
    bio = CKEditor5Field("biografía", blank=True, config_name="default")
    photo = models.ImageField("fotografía", upload_to="equipo/", blank=True)
    email = models.EmailField("email", blank=True)
    linkedin = models.URLField("LinkedIn", blank=True)
    show_on_home = models.BooleanField("mostrar en inicio", default=True)

    class Meta(Publishable.Meta):
        verbose_name = "integrante del equipo"
        verbose_name_plural = "equipo"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("core:team_detail", args=[self.slug])

    @property
    def initials(self):
        parts = self.name.split()
        return "".join(p[0] for p in parts[:2]).upper()

    @property
    def bio_lead(self):
        match = re.search(r"<p[^>]*>(.*?)</p>", self.bio or "", flags=re.I | re.S)
        if not match:
            return ""
        return re.sub(r"\s+", " ", strip_tags(match.group(1))).strip()

    @property
    def education(self):
        items = re.findall(r"<li>(.*?)</li>", self.bio or "", flags=re.I | re.S)
        lines = []
        for item in items:
            text = re.sub(r"\s+", " ", strip_tags(item)).strip()
            if text:
                lines.append(text)
        return lines

    @property
    def credentials(self):
        return [line for line in self.education if line.lower().startswith("diplom")]

    @property
    def practice_focus(self):
        match = re.search(
            r"(?:Áreas de ejercicio|Areas of practice)</h3>\s*<p[^>]*>(.*?)</p>",
            self.bio or "",
            flags=re.I | re.S,
        )
        if not match:
            return ""
        return re.sub(r"\s+", " ", strip_tags(match.group(1))).strip()


# --------------------------------------------------------------------------
# Testimonios, cifras, FAQ
# --------------------------------------------------------------------------
class Testimonial(Publishable):
    client_name = models.CharField("nombre", max_length=120)
    company = models.CharField("empresa", max_length=120, blank=True)
    position = models.CharField("cargo", max_length=120, blank=True)
    quote = models.TextField("testimonio")
    photo = models.ImageField("foto", upload_to="testimonios/", blank=True)
    rating = models.PositiveSmallIntegerField("valoración (1-5)", default=5, validators=[MinValueValidator(1), MaxValueValidator(5)])

    class Meta(Publishable.Meta):
        verbose_name = "testimonio"
        verbose_name_plural = "testimonios"

    def __str__(self):
        return f"{self.client_name} · {self.company}"

    @property
    def stars(self):
        return range(self.rating)


class Stat(Publishable):
    value = models.CharField("valor", max_length=20, help_text="Ej: 4, 10, 40%")
    label = models.CharField("etiqueta", max_length=120)
    icon = models.CharField("ícono", max_length=60, blank=True)

    class Meta(Publishable.Meta):
        verbose_name = "cifra destacada"
        verbose_name_plural = "cifras destacadas"

    def __str__(self):
        return f"{self.value} {self.label}"


class FAQ(Publishable):
    question = models.CharField("pregunta", max_length=255)
    answer = models.TextField("respuesta")
    plan = models.ForeignKey(Plan, verbose_name="plan relacionado", on_delete=models.SET_NULL, null=True, blank=True, related_name="faqs")

    class Meta(Publishable.Meta):
        verbose_name = "pregunta frecuente"
        verbose_name_plural = "preguntas frecuentes"

    def __str__(self):
        return self.question


# --------------------------------------------------------------------------
# Páginas editables (términos, privacidad, etc.)
# --------------------------------------------------------------------------
class Page(TimeStamped):
    title = models.CharField("título", max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    subtitle = models.CharField("subtítulo", max_length=255, blank=True)
    content = CKEditor5Field("contenido", config_name="default")
    is_published = models.BooleanField("publicada", default=True)
    show_in_footer = models.BooleanField("mostrar en pie de página", default=True)
    show_in_menu = models.BooleanField("mostrar en menú", default=False)
    order = models.PositiveIntegerField("orden", default=0)
    meta_description = models.CharField("meta descripción", max_length=160, blank=True)

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "página"
        verbose_name_plural = "páginas"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("core:page_detail", args=[self.slug])


# --------------------------------------------------------------------------
# Mensajes de contacto y newsletter
# --------------------------------------------------------------------------
class ContactMessage(TimeStamped):
    STATUS = [("new", "Nuevo"), ("in_progress", "En gestión"), ("closed", "Cerrado")]
    name = models.CharField("nombre", max_length=120)
    email = models.EmailField("email")
    phone = models.CharField("teléfono", max_length=30, blank=True)
    company = models.CharField("empresa", max_length=120, blank=True)
    subject = models.CharField("asunto", max_length=200, blank=True)
    message = models.TextField("mensaje")
    plan = models.ForeignKey(Plan, verbose_name="plan de interés", on_delete=models.SET_NULL, null=True, blank=True)
    service = models.ForeignKey(Service, verbose_name="servicio de interés", on_delete=models.SET_NULL, null=True, blank=True)
    source = models.CharField("origen", max_length=60, blank=True, default="web")
    privacy_accepted = models.BooleanField("aceptó la política de privacidad", default=False)
    status = models.CharField("estado", max_length=20, choices=STATUS, default="new")
    internal_notes = models.TextField("notas internas", blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "mensaje de contacto"
        verbose_name_plural = "mensajes de contacto"

    def __str__(self):
        return f"{self.name} · {self.created_at:%d/%m/%Y %H:%M}"


class NewsletterSubscriber(TimeStamped):
    email = models.EmailField("email", unique=True)
    name = models.CharField("nombre", max_length=120, blank=True)
    is_active = models.BooleanField("activo", default=True)
    privacy_accepted = models.BooleanField("aceptó el envío de publicaciones", default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "suscriptor newsletter"
        verbose_name_plural = "suscriptores newsletter"

    def __str__(self):
        return self.email
