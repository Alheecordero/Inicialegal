from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_heroslide_image_mobile"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sitesettings",
            name="hero_subtitle",
            field=models.TextField(
                blank=True,
                default="Acompañamos a emprendedores, e-commerce, startups y pymes en cada etapa de su empresa, con asesoría estratégica, clara y orientada a resultados.",
                verbose_name="subtítulo del hero",
            ),
        ),
    ]
