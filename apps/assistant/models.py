from django.db import models


class AssistantKnowledgeItem(models.Model):
    SOURCE_TYPES = [
        ("faq", "Pregunta frecuente"),
        ("service", "Servicio"),
        ("area", "Area de practica"),
        ("plan", "Plan"),
        ("page", "Pagina"),
        ("post", "Articulo"),
    ]

    source_type = models.CharField("tipo", max_length=20, choices=SOURCE_TYPES)
    source_id = models.PositiveBigIntegerField("ID de origen")
    title = models.CharField("titulo", max_length=240)
    summary = models.TextField("resumen", blank=True)
    content = models.TextField("contenido")
    url = models.CharField("URL", max_length=255, blank=True)
    is_active = models.BooleanField("activo", default=True)
    source_updated_at = models.DateTimeField("actualizado en origen", null=True, blank=True)
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["source_type", "title"]
        verbose_name = "contenido del asistente"
        verbose_name_plural = "contenidos del asistente"
        constraints = [
            models.UniqueConstraint(
                fields=["source_type", "source_id"],
                name="assistant_unique_source",
            )
        ]
        indexes = [
            models.Index(fields=["source_type", "is_active"]),
            models.Index(fields=["is_active", "updated_at"]),
        ]

    def __str__(self):
        return f"{self.get_source_type_display()} · {self.title}"


class AssistantConversation(models.Model):
    session_key = models.CharField("sesion", max_length=80, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField("IP", null=True, blank=True)
    user_agent = models.CharField("user agent", max_length=255, blank=True)
    created_at = models.DateTimeField("creada", auto_now_add=True)
    updated_at = models.DateTimeField("actualizada", auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "conversacion del asistente"
        verbose_name_plural = "conversaciones del asistente"

    def __str__(self):
        return self.session_key or f"Conversacion {self.pk}"


class AssistantMessage(models.Model):
    ROLES = [("user", "Usuario"), ("assistant", "Asistente")]

    conversation = models.ForeignKey(
        AssistantConversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField("rol", max_length=12, choices=ROLES)
    content = models.TextField("contenido")
    created_at = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "mensaje del asistente"
        verbose_name_plural = "mensajes del asistente"

    def __str__(self):
        return f"{self.get_role_display()} · {self.created_at:%d/%m/%Y %H:%M}"
