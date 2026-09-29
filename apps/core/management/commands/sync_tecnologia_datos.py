from django.core.management.base import BaseCommand

from apps.core.tecnologia_datos_content import sync_tecnologia_datos


class Command(BaseCommand):
    help = "Sincroniza la ficha Tecnología y datos y sus servicios desde tecnologia_datos_content."

    def handle(self, *args, **options):
        n = sync_tecnologia_datos(stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS(f"Listo: {n} servicios de Tecnología y datos."))
