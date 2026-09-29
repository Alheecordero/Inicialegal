from django.core.management.base import BaseCommand

from apps.core.corporativo_content import sync_corporativo


class Command(BaseCommand):
    help = "Sincroniza la ficha Corporativo y sus servicios (contacto y listados) desde corporativo_content."

    def handle(self, *args, **options):
        n = sync_corporativo(stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS(f"Listo: {n} servicios corporativos en el formulario de contacto."))
