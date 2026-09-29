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
    specs = [
        ("FAQ", ("question", "answer")),
        ("HeroSlide", ("kicker", "title", "subtitle", "primary_text", "secondary_text")),
        ("Page", ("title", "subtitle", "content", "meta_description")),
        ("Plan", (
            "name", "tagline", "summary", "problem_title", "problem_text",
            "solution_title", "solution_text", "price_note", "discount_badge",
            "discount_text", "cta_text",
        )),
        ("PlanFeature", ("title", "text")),
        ("PlanBenefit", ("title", "text")),
        ("PracticeArea", ("name", "short_description", "description")),
        ("Service", ("name", "short_description", "description", "price_note")),
        (
            "SiteSettings",
            (
                "tagline", "schedule", "whatsapp_message", "about_kicker", "about_title",
                "about_text", "cta_title", "cta_text", "cta_button_text", "footer_text",
                "meta_description", "cookie_consent_title", "cookie_consent_text",
            ),
        ),
        ("TeamMember", ("role", "specialty", "bio")),
    ]
    for model_name, fields in specs:
        _backfill_model(apps.get_model("core", model_name), fields)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_english_fields"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
