from decimal import Decimal

from django.db import migrations, models


AGUSTINAS_LAT = Decimal("-33.441480")
AGUSTINAS_LNG = Decimal("-70.657053")


def set_map_coordinates(apps, schema_editor):
    SiteSettings = apps.get_model("core", "SiteSettings")
    for settings in SiteSettings.objects.all():
        if settings.map_latitude is None and settings.map_longitude is None:
            settings.map_latitude = AGUSTINAS_LAT
            settings.map_longitude = AGUSTINAS_LNG
            settings.save(update_fields=["map_latitude", "map_longitude"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0016_address_agustinas"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="map_latitude",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                default=Decimal("-33.441480"),
                help_text="Pin del mapa (ej. -33.441480 para Agustinas 1442).",
                max_digits=9,
                null=True,
                validators=[],
                verbose_name="mapa · latitud",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="map_longitude",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                default=Decimal("-70.657053"),
                help_text="Pin del mapa (ej. -70.657053 para Agustinas 1442).",
                max_digits=9,
                null=True,
                validators=[],
                verbose_name="mapa · longitud",
            ),
        ),
        migrations.RunPython(set_map_coordinates, migrations.RunPython.noop),
    ]
