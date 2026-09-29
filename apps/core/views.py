import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.translation import get_language, gettext as _
from django.views.decorators.http import require_POST

from apps.blog.models import Post

logger = logging.getLogger(__name__)

from .contact_email import contact_email_context, newsletter_email_context
from .forms import ContactForm, NewsletterForm
from .offers import build_plan_offer
from .models import (
    FAQ,
    NewsletterSubscriber,
    Page,
    Plan,
    PracticeArea,
    Service,
    HeroSlide,
    Stat,
    TeamMember,
    Testimonial,
)


def home(request):
    context = {
        "stats": Stat.objects.filter(is_active=True),
        "areas": PracticeArea.objects.filter(is_active=True, show_on_home=True),
        "services": Service.objects.filter(is_active=True, is_featured=True)[:6],
        **build_plan_offer(Plan.objects.filter(is_active=True).prefetch_related("features", "benefits")),
        "team": TeamMember.objects.filter(is_active=True, show_on_home=True).prefetch_related("areas")[:4],
        "testimonials": Testimonial.objects.filter(is_active=True)[:6],
        "faqs": FAQ.objects.filter(is_active=True, plan__isnull=True)[:6],
        "posts": Post.published.select_related("category", "author")[:3],
        "hero_slides": HeroSlide.objects.filter(is_active=True),
    }
    return render(request, "core/home.html", context)


def about(request):
    context = {
        "team": TeamMember.objects.filter(is_active=True).prefetch_related("areas"),
        "stats": Stat.objects.filter(is_active=True),
        "areas": PracticeArea.objects.filter(is_active=True),
        "testimonials": Testimonial.objects.filter(is_active=True)[:3],
    }
    return render(request, "core/about.html", context)


def service_list(request):
    services = Service.objects.filter(is_active=True).select_related("area")
    areas = PracticeArea.objects.filter(is_active=True)
    area_slug = request.GET.get("area")
    current_area = None
    if area_slug:
        current_area = areas.filter(slug=area_slug).first()
        if current_area:
            services = services.filter(area=current_area)
    return render(request, "core/service_list.html", {"services": services, "areas": areas, "current_area": current_area})


def service_detail(request, slug):
    service = get_object_or_404(Service.objects.select_related("area"), slug=slug, is_active=True)
    related = Service.objects.filter(is_active=True).exclude(pk=service.pk)
    if service.area:
        related = related.filter(area=service.area)
    context = {
        "service": service,
        "related": related[:3],
        "featured_plan": Plan.objects.filter(is_active=True, is_featured=True).first(),
    }
    return render(request, "core/service_detail.html", context)


_LEGACY_AREAS = {
    "derecho-societario": "corporativo",
    "derecho-civil": "corporativo",
}


def area_detail(request, slug):
    if slug in _LEGACY_AREAS:
        return redirect("core:area_detail", _LEGACY_AREAS[slug])
    area = get_object_or_404(PracticeArea, slug=slug, is_active=True)
    context = {
        "area": area,
        "services": area.services.filter(is_active=True),
        "members": area.members.filter(is_active=True),
        "other_areas": PracticeArea.objects.filter(is_active=True).exclude(pk=area.pk),
        "posts": Post.published.filter(areas=area)[:3],
    }
    return render(request, "core/area_detail.html", context)


def plan_list(request):
    offer = build_plan_offer(Plan.objects.filter(is_active=True).prefetch_related("features", "benefits"))
    return render(request, "core/plan_list.html", offer)


def plan_detail(request, slug):
    offer = build_plan_offer(
        Plan.objects.filter(is_active=True).prefetch_related("features", "benefits", "faqs")
    )
    plan = next((item for item in offer["plans"] if item.slug == slug), None)
    if plan is None:
        plan = get_object_or_404(Plan, slug=slug, is_active=True)
    context = {
        "plan": plan,
        "faqs": plan.faqs.filter(is_active=True),
        "areas": PracticeArea.objects.filter(is_active=True),
        "other_plans": [item for item in offer["plans"] if item.pk != plan.pk],
        "shared_features": offer["shared_features"],
        "has_difference": offer["has_difference"],
    }
    return render(request, "core/plan_detail.html", context)


def team_list(request):
    members = TeamMember.objects.filter(is_active=True).prefetch_related("areas")
    return render(request, "core/team_list.html", {"team": members})


def _posts_by_member(member, limit=3):
    """Artículos cuyo nombre de autor cabe dentro del nombre del integrante."""
    name = member.name.casefold()
    found = []
    for post in Post.published.all():
        tokens = [token for token in post.author_name.casefold().split() if len(token) > 2]
        if len(tokens) >= 2 and all(token in name for token in tokens):
            found.append(post)
        if len(found) >= limit:
            break
    return found


def team_detail(request, slug):
    member = get_object_or_404(TeamMember.objects.prefetch_related("areas"), slug=slug, is_active=True)
    return render(request, "core/team_detail.html", {"member": member, "posts": _posts_by_member(member)})


def faq_list(request):
    faqs = FAQ.objects.filter(is_active=True).select_related("plan")
    # Generales primero, luego agrupadas por plan (necesario para {% regroup %})
    faqs = sorted(faqs, key=lambda f: (f.plan_id or 0, f.order, f.pk))
    return render(request, "core/faq.html", {"faqs": faqs})


def page_detail(request, slug):
    page = get_object_or_404(Page, slug=slug, is_published=True)
    return render(request, "core/page_detail.html", {"page": page})


def contact(request):
    initial = {}
    plan_slug = request.GET.get("plan")
    service_slug = request.GET.get("servicio")
    if plan_slug:
        plan = Plan.objects.filter(slug=plan_slug, is_active=True).first()
        if plan:
            initial["plan"] = plan
            initial["subject"] = f"Interés en {plan.name}"
    if service_slug:
        service = Service.objects.filter(slug=service_slug, is_active=True).first()
        if service:
            initial["service"] = service
            initial["subject"] = f"Consulta sobre {service.name}"

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.source = request.POST.get("source", "web")
            msg.privacy_accepted = True
            msg.save()
            _notify_contact(msg)
            messages.success(request, _("Recibimos su mensaje. Le contactaremos a la brevedad."))
            return redirect("core:contact_success")
        messages.error(request, _("Revise los campos marcados e inténtelo nuevamente."))
    else:
        form = ContactForm(initial=initial)
    return render(request, "core/contact.html", {"form": form})


def contact_success(request):
    return render(request, "core/contact_success.html", {"posts": Post.published.all()[:3]})


def _send_branded_mail(subject, text_template, html_template, to, ctx, *, reply_to=None, from_email=None):
    body = render_to_string(text_template, ctx)
    mail = EmailMultiAlternatives(
        subject,
        body,
        from_email or settings.DEFAULT_FROM_EMAIL,
        to,
        reply_to=reply_to,
    )
    mail.attach_alternative(render_to_string(html_template, ctx), "text/html")
    mail.send(fail_silently=False)


def _send_contact_mail(subject, text_template, html_template, to, reply_to, ctx, from_email=None):
    _send_branded_mail(subject, text_template, html_template, to, ctx, reply_to=reply_to, from_email=from_email)


def _notify_contact(msg):
    """Avisa al estudio y confirma la recepción a quien envió la solicitud."""
    office = settings.CONTACT_NOTIFY_EMAIL
    ctx = contact_email_context(msg)
    try:
        _send_contact_mail(
            f"[Web Inicia Legal] Nuevo contacto: {msg.name}",
            "core/emails/contact_notification.txt",
            "core/emails/contact_notification.html",
            [office],
            [msg.email] if msg.email else None,
            ctx,
        )
    except Exception:
        logger.exception("No se pudo avisar a %s del contacto %s", office, msg.pk)
    if not msg.email or msg.email.lower() == office.lower():
        return
    try:
        english = (get_language() or "").startswith("en")
        if english:
            _send_contact_mail(
                "Confirmation of receipt · Inicia Legal",
                "core/emails/contact_confirmation_en.txt",
                "core/emails/contact_confirmation_en.html",
                [msg.email],
                [office],
                ctx,
                from_email=settings.CONTACT_CLIENT_FROM_EMAIL,
            )
        else:
            _send_contact_mail(
                "Confirmación de recepción · Inicia Legal",
                "core/emails/contact_confirmation.txt",
                "core/emails/contact_confirmation.html",
                [msg.email],
                [office],
                ctx,
                from_email=settings.CONTACT_CLIENT_FROM_EMAIL,
            )
    except Exception:
        logger.exception("No se pudo confirmar la solicitud %s a %s", msg.pk, msg.email)


def _notify_newsletter_subscribe(sub, *, already_listed: bool):
    office = settings.CONTACT_NOTIFY_EMAIL
    english = (get_language() or "").startswith("en")
    ctx = newsletter_email_context(sub, already_listed=already_listed)
    if english:
        ctx["blog_url"] = f"{ctx['site_url']}/en/blog/"
    if already_listed:
        subject = "Newsletter · Inicia Legal" if english else "Newsletter · Inicia Legal"
        text_t = "core/emails/newsletter_subscribe_en.txt" if english else "core/emails/newsletter_subscribe.txt"
        html_t = "core/emails/newsletter_subscribe_en.html" if english else "core/emails/newsletter_subscribe.html"
    else:
        subject = "Newsletter subscription · Inicia Legal" if english else "Confirmación de suscripción al newsletter · Inicia Legal"
        text_t = "core/emails/newsletter_subscribe_en.txt" if english else "core/emails/newsletter_subscribe.txt"
        html_t = "core/emails/newsletter_subscribe_en.html" if english else "core/emails/newsletter_subscribe.html"
    try:
        _send_branded_mail(
            subject,
            text_t,
            html_t,
            [sub.email],
            ctx,
            reply_to=[office],
            from_email=settings.CONTACT_CLIENT_FROM_EMAIL,
        )
    except Exception:
        logger.exception("No se pudo confirmar la suscripción newsletter %s", sub.pk)


@require_POST
def newsletter_subscribe(request):
    form = NewsletterForm(request.POST)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    if form.is_valid():
        email = form.cleaned_data["email"]
        try:
            sub, created = NewsletterSubscriber.objects.get_or_create(email=email)
            already_listed = not created and sub.is_active
            sub.privacy_accepted = True
            sub.is_active = True
            sub.save(update_fields=["is_active", "privacy_accepted"])
            _notify_newsletter_subscribe(sub, already_listed=already_listed)
            text = _("Gracias. Su suscripción quedó registrada.") if not already_listed else _("Ese correo ya estaba suscrito. Gracias.")
            ok = True
        except IntegrityError:
            text, ok = _("Ese correo ya estaba suscrito."), True
    else:
        if form.errors.get("accept") and not form.errors.get("email"):
            text = _("Debe aceptar el tratamiento de su correo para suscribirse.")
        else:
            text = _("Ingrese un correo válido.")
        ok = False
    if is_ajax:
        return JsonResponse({"ok": ok, "message": text})
    (messages.success if ok else messages.error)(request, text)
    return redirect(request.META.get("HTTP_REFERER", "/"))


def error_404(request, exception=None):
    return render(request, "404.html", status=404)


def error_500(request):
    return render(request, "500.html", status=500)
