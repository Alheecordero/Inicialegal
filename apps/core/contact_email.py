from django.conf import settings

from .models import ContactMessage, NewsletterSubscriber, SiteSettings

SOURCE_LABELS = {
    "web": "Sitio web",
    "formulario-contacto": "Formulario de contacto",
}


def _email_logo_url(site: SiteSettings, base: str, *, white: bool = False) -> str:
    field = site.logo_white if white else site.logo
    if field:
        return f"{base}{field.url}"
    return f"{base}/static/img/logo-white.png" if white else f"{base}/static/img/logo.png"


def site_email_context() -> dict:
    site = SiteSettings.load()
    base = settings.SITE_URL.rstrip("/")
    privacy = (site.privacy_policy_url or "/p/privacidad/").strip()
    if not privacy.startswith("http"):
        privacy = f"{base}{privacy if privacy.startswith('/') else '/' + privacy}"
    return {
        "site": site,
        "site_name": site.site_name,
        "site_url": base,
        "logo_url": _email_logo_url(site, base, white=True),
        "office_email": settings.CONTACT_NOTIFY_EMAIL,
        "privacy_url": privacy,
    }


def contact_email_context(msg: ContactMessage) -> dict:
    admin = settings.ADMIN_PATH.strip("/")
    source = (msg.source or "web").strip()
    ctx = site_email_context()
    base = ctx["site_url"]
    ctx.update(
        msg=msg,
        reference=f"IL-{msg.created_at:%Y}-{msg.pk:05d}",
        admin_url=f"{base}/{admin}/core/contactmessage/{msg.pk}/change/",
        status_label=dict(ContactMessage.STATUS).get(msg.status, msg.status),
        source_label=SOURCE_LABELS.get(source, source or "Sitio web"),
        plan_name=msg.plan.name if msg.plan_id else "",
        service_name=msg.service.name if msg.service_id else "",
    )
    return ctx


def newsletter_email_context(sub: NewsletterSubscriber, *, already_listed: bool) -> dict:
    ctx = site_email_context()
    base = ctx["site_url"]
    ctx.update(
        sub=sub,
        email=sub.email,
        already_listed=already_listed,
        reference=f"NL-{sub.pk:05d}",
        blog_url=f"{base}/blog/",
    )
    return ctx
