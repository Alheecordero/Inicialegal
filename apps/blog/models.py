import math
import re

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field

from apps.core.models import PracticeArea, unique_slugify


class Category(models.Model):
    name = models.CharField("nombre", max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField("descripción", blank=True)
    color = models.CharField("color", max_length=7, default="#B5924C", help_text="Color hexadecimal, ej: #B5924C")
    order = models.PositiveIntegerField("orden", default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "categoría"
        verbose_name_plural = "categorías"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:category", args=[self.slug])

    @property
    def published_count(self):
        return self.posts.filter(status=Post.PUBLISHED, published_at__lte=timezone.now()).count()


class Tag(models.Model):
    name = models.CharField("nombre", max_length=60, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "etiqueta"
        verbose_name_plural = "etiquetas"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:tag", args=[self.slug])


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Post.PUBLISHED, published_at__lte=timezone.now())


class Post(models.Model):
    DRAFT, PUBLISHED = "draft", "published"
    STATUS = [(DRAFT, "Borrador"), (PUBLISHED, "Publicado")]

    title = models.CharField("título", max_length=200)
    slug = models.SlugField(unique=True, blank=True, max_length=220)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="autor", on_delete=models.SET_NULL, null=True, blank=True, related_name="posts")
    author_display = models.CharField("nombre de autor a mostrar", max_length=120, blank=True, help_text="Si se deja vacío se usa el nombre del usuario o 'Equipo Inicia Legal'.")
    category = models.ForeignKey(Category, verbose_name="categoría", on_delete=models.SET_NULL, null=True, blank=True, related_name="posts")
    tags = models.ManyToManyField(Tag, verbose_name="etiquetas", blank=True, related_name="posts")
    areas = models.ManyToManyField(PracticeArea, verbose_name="áreas relacionadas", blank=True, related_name="posts")
    excerpt = models.TextField("extracto", max_length=400, blank=True, help_text="Resumen breve para listados y redes. Si se deja vacío se genera automáticamente.")
    content = CKEditor5Field("contenido", config_name="default")
    cover_image = models.ImageField("imagen de portada", upload_to="blog/%Y/%m/", blank=True)
    cover_caption = models.CharField("leyenda de la imagen", max_length=200, blank=True)
    status = models.CharField("estado", max_length=10, choices=STATUS, default=DRAFT)
    published_at = models.DateTimeField("fecha de publicación", default=timezone.now, help_text="Puede programarse a futuro.")
    is_featured = models.BooleanField("destacado", default=False)
    allow_comments = models.BooleanField("permitir comentarios", default=True)
    views = models.PositiveIntegerField("visitas", default=0, editable=False)
    meta_title = models.CharField("meta título", max_length=70, blank=True)
    meta_description = models.CharField("meta descripción", max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "artículo"
        verbose_name_plural = "artículos"
        indexes = [models.Index(fields=["status", "published_at"])]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.title)
        if not self.excerpt and self.content:
            text = re.sub(r"\s+", " ", strip_tags(self.content)).strip()
            self.excerpt = (text[:280] + "…") if len(text) > 280 else text
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:post_detail", args=[self.slug])

    @property
    def is_published(self):
        return self.status == self.PUBLISHED and self.published_at <= timezone.now()

    @property
    def author_name(self):
        if self.author_display:
            return self.author_display
        if self.author:
            return self.author.get_full_name() or self.author.get_username()
        return "Equipo Inicia Legal"

    @property
    def reading_time(self):
        words = len(strip_tags(self.content or "").split())
        return max(1, math.ceil(words / 200))

    @property
    def seo_title(self):
        return self.meta_title or self.title

    @property
    def seo_description(self):
        return self.meta_description or self.excerpt

    def approved_comments(self):
        return self.comments.filter(is_approved=True, parent__isnull=True)


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies")
    name = models.CharField("nombre", max_length=100)
    email = models.EmailField("email")
    body = models.TextField("comentario", max_length=2000)
    is_approved = models.BooleanField("aprobado", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "comentario"
        verbose_name_plural = "comentarios"

    def __str__(self):
        return f"{self.name} en {self.post}"

    @property
    def initials(self):
        return "".join(p[0] for p in self.name.split()[:2]).upper()
