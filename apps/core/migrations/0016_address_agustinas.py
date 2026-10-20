from django.db import migrations, models


NEW_ADDRESS = "Agustinas N°1442, oficina N°302, Torre A"
NEW_CITY = "Santiago"
PRIVACY_OLD = "Los Militares N.° 5620, oficina N.° 905, comuna de Las Condes."
PRIVACY_NEW = "Agustinas N.° 1442, oficina N.° 302, Torre A, Santiago."


def forwards(apps, schema_editor):
    SiteSettings = apps.get_model("core", "SiteSettings")
    Page = apps.get_model("core", "Page")
    for settings in SiteSettings.objects.all():
        changed = []
        if not settings.address or "Militares" in settings.address:
            settings.address = NEW_ADDRESS
            changed.append("address")
        if settings.city in ("Las Condes, Santiago", "Santiago, Chile"):
            settings.city = NEW_CITY
            changed.append("city")
        if settings.meta_description and "Las Condes" in settings.meta_description:
            settings.meta_description = settings.meta_description.replace("Las Condes", "Santiago")
            changed.append("meta_description")
        if changed:
            settings.save(update_fields=changed)
    for page in Page.objects.filter(content__icontains="Militares"):
        page.content = page.content.replace(PRIVACY_OLD, PRIVACY_NEW).replace(
            "Los Militares N°5620, oficina N°905",
            NEW_ADDRESS,
        )
        page.save(update_fields=["content"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_restore_base_content_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sitesettings",
            name="address",
            field=models.CharField(
                blank=True,
                default="Agustinas N°1442, oficina N°302, Torre A",
                max_length=200,
                verbose_name="dirección",
            ),
        ),
        migrations.AlterField(
            model_name="sitesettings",
            name="city",
            field=models.CharField(blank=True, default="Santiago", max_length=100, verbose_name="ciudad"),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
