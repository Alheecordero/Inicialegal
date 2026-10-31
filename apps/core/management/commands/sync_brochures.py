from django.core.management.base import BaseCommand

from apps.core.management.commands.seed import attach_image
from apps.core.models import Plan

BROCHURES = {
    "plan-legal-pyme": "plan-legal-pyme.pdf",
    "plan-legal-advance": "plan-legal-advance.pdf",
}


class Command(BaseCommand):
    help = "Actualiza los brochures PDF de los planes desde seed_media (no toca los que subió el cliente)."

    def handle(self, *args, **options):
        updated = 0
        for plan in Plan.objects.filter(slug__in=BROCHURES):
            if attach_image(plan, "brochure", BROCHURES[plan.slug]):
                updated += 1
                self.stdout.write(f"· {plan.slug}: brochure actualizado")
        self.stdout.write(self.style.SUCCESS(f"Listo: {updated} brochures actualizados."))
