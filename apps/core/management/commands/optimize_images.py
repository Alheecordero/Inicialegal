"""Genera versiones WebP al tamaño en que se muestran y apunta los campos a ellas."""

import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import ImageField
from PIL import Image, ImageOps

from apps.blog.models import Post
from apps.core.models import HeroSlide, Plan, PracticeArea, Service, SiteSettings, TeamMember, Testimonial


def _limit(name):
    low = name.lower()
    base = os.path.basename(low)
    if "logo" in base:
        return 640, 82
    if low.startswith("equipo/"):
        return 720, 80
    if low.startswith("areas/"):
        return 1400, 72
    if low.startswith("blog/"):
        return 1200, 74
    if "hero" in low:
        return 1600, 72
    return 1400, 74


def _to_webp(src, limit, quality):
    image = ImageOps.exif_transpose(Image.open(src))
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
    width, height = image.size
    edge = max(width, height)
    if edge > limit:
        scale = limit / edge
        image = image.resize((max(1, round(width * scale)), max(1, round(height * scale))), Image.Resampling.LANCZOS)
    dest = os.path.splitext(src)[0] + ".webp"
    image.save(dest, "WEBP", quality=quality, method=6)
    return dest, os.path.getsize(src), os.path.getsize(dest)


class Command(BaseCommand):
    help = "Reduce las fotos del sitio y actualiza la base para servir WebP."

    def handle(self, *args, **options):
        self._media()
        self._static()

    def _media(self):
        models = (SiteSettings, HeroSlide, PracticeArea, Service, Plan, TeamMember, Testimonial, Post)
        for model in models:
            fields = [f.name for f in model._meta.fields if isinstance(f, ImageField)]
            if not fields:
                continue
            for obj in model.objects.all():
                for field in fields:
                    file = getattr(obj, field)
                    name = getattr(file, "name", "") or ""
                    if not name or name.lower().endswith(".webp"):
                        continue
                    src = os.path.join(settings.MEDIA_ROOT, name)
                    if not os.path.isfile(src):
                        self.stdout.write(f"falta {name}")
                        continue
                    limit, quality = _limit(name)
                    dest, before, after = _to_webp(src, limit, quality)
                    if after >= before * 0.9:
                        os.remove(dest)
                        self.stdout.write(f"sin ganancia {name}")
                        continue
                    rel = os.path.relpath(dest, settings.MEDIA_ROOT)
                    setattr(obj, field, rel)
                    obj.save(update_fields=[field])
                    self.stdout.write(f"{name}: {before} → {after}")

    def _static(self):
        root = settings.BASE_DIR / "static" / "img"
        jobs = (
            ("logo.png", 480, None),
            ("logo-white.png", 480, None),
            ("blog-portada.jpg", 1200, 70),
            ("footer-justicia.jpg", 960, 62),
        )
        for filename, limit, quality in jobs:
            src = root / filename
            if not src.is_file():
                continue
            image = ImageOps.exif_transpose(Image.open(src))
            width, height = image.size
            if width > limit:
                scale = limit / width
                image = image.resize((limit, max(1, round(height * scale))), Image.Resampling.LANCZOS)
            if quality is None:
                if image.mode not in ("RGB", "RGBA"):
                    image = image.convert("RGBA")
                image.save(src, "PNG", optimize=True)
                self.stdout.write(f"{filename}: {src.stat().st_size}")
                continue
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGB")
            dest = src.with_suffix(".webp")
            image.save(dest, "WEBP", quality=quality, method=6)
            self.stdout.write(f"{filename} → {dest.name}: {dest.stat().st_size} ({image.size[0]}x{image.size[1]})")
