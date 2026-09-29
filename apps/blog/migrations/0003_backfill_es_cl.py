"""Copia el contenido español de las columnas base a *_es_cl tras la migración i18n."""

from django.db import migrations


def _blank(value):
    return value is None or (isinstance(value, str) and not value.strip())


def _backfill_model(Model, fields):
    for obj in Model.objects.all():
        update_fields = []
        for name in fields:
            es_attr = f"{name}_es_cl"
            if not hasattr(obj, es_attr):
                continue
            if not _blank(getattr(obj, es_attr)):
                continue
            base = getattr(obj, name, None)
            if _blank(base):
                continue
            setattr(obj, es_attr, base)
            update_fields.append(es_attr)
        if update_fields:
            obj.save(update_fields=update_fields)


def forwards(apps, schema_editor):
    _backfill_model(apps.get_model("blog", "Category"), ("name", "description"))
    _backfill_model(
        apps.get_model("blog", "Post"),
        ("title", "excerpt", "content", "meta_title", "meta_description", "cover_caption"),
    )


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0002_english_fields"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
