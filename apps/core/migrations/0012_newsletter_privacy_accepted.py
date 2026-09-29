from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_contactmessage_privacy_accepted"),
    ]

    operations = [
        migrations.AddField(
            model_name="newslettersubscriber",
            name="privacy_accepted",
            field=models.BooleanField(default=False, verbose_name="aceptó el envío de publicaciones"),
        ),
    ]
