from django.core.management.base import BaseCommand

from apps.core.commercial_copy import apply_all


class Command(BaseCommand):
    help = "Actualiza textos comerciales en SiteSettings, carrusel, áreas y planes (idempotente)."

    def handle(self, *args, **options):
        result = apply_all()
        self.stdout.write(
            self.style.SUCCESS(
                "Copy comercial actualizado "
                f"(slides: {result['hero_slides']}, áreas: {result['areas']}, planes: {result['plans']})."
            )
        )
