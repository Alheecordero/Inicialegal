"""Tras retirar modeltranslation, asegura que las columnas base tengan el texto español."""

from django.db import migrations


def _blank(value):
    return value is None or (isinstance(value, str) and not value.strip())


def _sync_model(Model, fields):
    for obj in Model.objects.all():
        update_fields = []
        for name in fields:
            if _blank(getattr(obj, name, None)):
                es_val = getattr(obj, f"{name}_es_cl", None)
                if not _blank(es_val):
                    setattr(obj, name, es_val)
                    update_fields.append(name)
            elif hasattr(obj, f"{name}_es_cl"):
                es_val = getattr(obj, f"{name}_es_cl")
                if _blank(es_val):
                    setattr(obj, f"{name}_es_cl", getattr(obj, name))
                    update_fields.append(f"{name}_es_cl")
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
        _sync_model(apps.get_model("core", model_name), fields)

    _sync_model(apps.get_model("blog", "Category"), ("name", "description"))
    _sync_model(
        apps.get_model("blog", "Post"),
        ("title", "excerpt", "content", "meta_title", "meta_description", "cover_caption"),
    )


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0003_backfill_es_cl"),
        ("core", "0014_backfill_es_cl"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
