from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_hero_subtitle_empresa"),
    ]

    operations = [
        migrations.AddField(
            model_name="contactmessage",
            name="privacy_accepted",
            field=models.BooleanField(default=False, verbose_name="aceptó la política de privacidad"),
        ),
    ]
