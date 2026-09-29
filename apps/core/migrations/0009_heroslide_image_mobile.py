from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_hero_kicker_empresa"),
    ]

    operations = [
        migrations.AddField(
            model_name="heroslide",
            name="image_mobile",
            field=models.ImageField(
                blank=True,
                help_text="Opcional. Cuadrada o vertical. Si se deja vacía se usa la imagen principal.",
                upload_to="site/hero/",
                verbose_name="imagen (móvil)",
            ),
        ),
    ]
