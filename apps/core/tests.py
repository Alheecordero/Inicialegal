from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .legacy_redirects import LEGACY_PATHS
from .models import FAQ, SiteSettings


@override_settings(ALLOWED_HOSTS=["testserver"])
class CorePageTests(TestCase):
    def test_faq_page_renders(self):
        FAQ.objects.create(question="¿La primera reunión tiene costo?", answer="No tiene costo inicial.")

        response = self.client.get(reverse("core:faq"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Preguntas frecuentes")

    def test_map_urls_use_coordinates_for_exact_pin(self):
        site = SiteSettings.load()
        site.address = "Agustinas N°1442, oficina N°302, Torre A"
        site.city = "Santiago"
        site.map_embed_url = ""
        site.map_latitude = "-33.441480"
        site.map_longitude = "-70.657053"
        site.save()

        self.assertIn("-33.441480,-70.657053", site.maps_embed_src)
        self.assertIn("-33.441480,-70.657053", site.maps_directions_url)
        self.assertIn("-33.441480,-70.657053", site.maps_place_url)
        self.assertIn("Agustinas", site.maps_location)


class LegacyRedirectTests(SimpleTestCase):
    def test_old_urls_redirect_permanently(self):
        samples = {
            "/inicio/": "/",
            "/privacy-policy/": "/p/privacidad/",
            "/landing-page-tributario/": "/areas/derecho-tributario/",
            "/2025/09/15/registro-de-marcas-ante-el-inapi/": "/blog/registro-de-marcas-en-inapi/",
            "/2025/09/15/errores-comunes-al-emprender-en-chile-y-como-evitarlos/": (
                "/blog/errores-comunes-al-emprender-en-chile-y-como-evitarlos/"
            ),
        }
        for source, target in samples.items():
            response = self.client.get(source)
            self.assertRedirects(response, target, status_code=301, fetch_redirect_response=False)

    def test_every_legacy_path_is_a_permanent_redirect(self):
        for source, target in LEGACY_PATHS.items():
            response = self.client.get("/" + source)
            self.assertEqual(response.status_code, 301)
            self.assertEqual(response["Location"], target)


@override_settings(
    ALLOWED_HOSTS=["testserver"],
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    CONTACT_NOTIFY_EMAIL="contacto@inicialegal.cl",
)
class AntiSpamTests(TestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()

    def _contact(self, **extra):
        data = {
            "name": "Ana Pérez",
            "email": "ana@example.com",
            "subject": "Consulta",
            "message": "Necesito ayuda con un contrato.",
            "accept": "on",
            "website": "",
        }
        data.update(extra)
        return self.client.post(reverse("core:contact"), data, REMOTE_ADDR="203.0.113.5")

    def test_honeypot_is_a_text_field_and_rejects_bots(self):
        from .models import ContactMessage

        page = self.client.get(reverse("core:contact"))
        self.assertContains(page, 'type="text" name="website"')

        self._contact(website="http://spam.example")
        self.assertFalse(ContactMessage.objects.exists())

    def test_unknown_source_is_stored_as_web(self):
        from .models import ContactMessage

        self._contact(source="x" * 200)
        self.assertEqual(ContactMessage.objects.get().source, "web")

    def test_contact_is_limited_per_ip(self):
        from .models import ContactMessage
        from .views import CONTACT_PER_IP_HOUR

        for _ in range(CONTACT_PER_IP_HOUR):
            self._contact()
        response = self._contact()

        self.assertEqual(response.status_code, 429)
        self.assertEqual(ContactMessage.objects.count(), CONTACT_PER_IP_HOUR)

    def test_confirmation_mails_per_recipient_are_capped(self):
        from django.core import mail

        from .views import MAILS_PER_RECIPIENT_DAY

        for i in range(MAILS_PER_RECIPIENT_DAY + 1):
            self.client.post(
                reverse("core:contact"),
                {"name": "Ana", "email": "victima@example.com", "message": "x", "accept": "on"},
                REMOTE_ADDR=f"203.0.113.{i + 10}",
            )
        to_victim = [m for m in mail.outbox if m.to == ["victima@example.com"]]
        self.assertEqual(len(to_victim), MAILS_PER_RECIPIENT_DAY)

    def test_newsletter_does_not_resend_to_subscribed_address(self):
        from django.core import mail

        url = reverse("core:newsletter")
        data = {"email": "lector@example.com", "accept": "on"}
        self.client.post(url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.client.post(url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

        self.assertEqual(len(mail.outbox), 1)

    def test_newsletter_ignores_foreign_referer(self):
        response = self.client.post(
            reverse("core:newsletter"),
            {"email": "lector@example.com", "accept": "on"},
            HTTP_REFERER="https://evil.example/",
        )
        self.assertEqual(response["Location"], "/")

    def test_client_ip_ignores_cf_connecting_ip(self):
        from django.test import RequestFactory

        from .ratelimit import client_ip

        request = RequestFactory().get("/", HTTP_CF_CONNECTING_IP="1.2.3.4", HTTP_X_REAL_IP="198.51.100.7")
        self.assertEqual(client_ip(request), "198.51.100.7")


class SeoTests(TestCase):
    def test_home_has_single_h1_and_legal_service_ld(self):
        from .models import HeroSlide

        for i in range(3):
            HeroSlide.objects.create(key=f"s{i}", title=f"Título {i}", order=i, is_active=True)
        html = self.client.get("/").content.decode()
        self.assertEqual(html.count("<h1"), 1)
        self.assertIn('"@type": "LegalService"', html)

    def test_hreflang_ignores_query_string(self):
        html = self.client.get("/?utm_source=x").content.decode()
        self.assertIn('hreflang="es-CL" href="http', html)
        self.assertNotIn("utm_source", html.split('hreflang="es-CL"')[1].split(">")[0])

    def test_legacy_area_redirect_is_permanent(self):
        resp = self.client.get(reverse("core:area_detail", args=["derecho-societario"]))
        self.assertEqual(resp.status_code, 301)


@override_settings(TURNSTILE_SITE_KEY="site", TURNSTILE_SECRET_KEY="secret")
class TurnstileTests(TestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()

    def _post_contact(self, **extra):
        data = {"name": "Ana", "email": "ana@example.com", "subject": "Hola", "message": "Consulta", "accept": "on", **extra}
        return self.client.post(reverse("core:contact"), data)

    def test_widget_rendered_when_enabled(self):
        html = self.client.get(reverse("core:contact")).content.decode()
        self.assertIn('class="cf-turnstile" data-sitekey="site"', html)
        self.assertIn("challenges.cloudflare.com/turnstile/v0/api.js", html)

    def test_contact_without_token_is_rejected(self):
        from .models import ContactMessage

        resp = self._post_contact()
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(ContactMessage.objects.exists())

    def test_contact_with_valid_token_is_saved(self):
        from unittest import mock

        from .models import ContactMessage

        with mock.patch("apps.core.turnstile.urlopen") as fake:
            fake.return_value.__enter__.return_value.read.return_value = b'{"success": true}'
            resp = self._post_contact(**{"cf-turnstile-response": "tok"})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(ContactMessage.objects.exists())

    def test_newsletter_rejects_invalid_token(self):
        from unittest import mock

        with mock.patch("apps.core.turnstile.urlopen") as fake:
            fake.return_value.__enter__.return_value.read.return_value = b'{"success": false}'
            resp = self.client.post(
                reverse("core:newsletter"),
                {"email": "a@example.com", "accept": "on", "cf-turnstile-response": "tok"},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
        self.assertEqual(resp.status_code, 400)


class Ley21719DisabledTests(TestCase):
    def test_guide_is_off_by_default(self):
        self.assertEqual(self.client.get("/ley-21719/").status_code, 404)
        self.assertEqual(self.client.get("/ley-21719/checklist/").status_code, 404)
        self.assertNotContains(self.client.get("/sitemap.xml"), "/ley-21719/")


@override_settings(LEY_21719_PAGE_ENABLED=True)
class Ley21719Tests(TestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()

    def test_landing_renders_with_faq_schema_and_lead_form(self):
        resp = self.client.get(reverse("core:ley_21719"))
        self.assertContains(resp, '"@type":"FAQPage"')
        self.assertContains(resp, 'name="lead" value="checklist-21719"')
        self.assertContains(resp, "<h1", count=1)

    def test_landing_is_in_sitemap(self):
        self.assertContains(self.client.get("/sitemap.xml"), "/ley-21719/")

    def test_checklist_has_17_items_and_is_noindex(self):
        resp = self.client.get(reverse("core:ley_21719_checklist"))
        self.assertContains(resp, 'type="checkbox" id="ck', count=17)
        self.assertContains(resp, 'content="noindex, follow"')

    def test_subscribing_from_landing_returns_checklist(self):
        from .models import NewsletterSubscriber

        resp = self.client.post(
            reverse("core:newsletter"),
            {"email": "pyme@example.com", "accept": "on", "lead": "checklist-21719"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.json()["download"], reverse("core:ley_21719_checklist"))
        self.assertTrue(NewsletterSubscriber.objects.filter(email="pyme@example.com").exists())

    def test_plain_newsletter_has_no_download(self):
        resp = self.client.post(
            reverse("core:newsletter"),
            {"email": "otro@example.com", "accept": "on"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.json()["download"], "")

    def test_days_left(self):
        import datetime

        from .ley_21719_content import days_left

        self.assertEqual(days_left(datetime.date(2026, 11, 1)), 30)
        self.assertEqual(days_left(datetime.date(2027, 1, 1)), 0)


class LegacyDatedPostTests(TestCase):
    def test_unknown_dated_url_goes_to_blog(self):
        resp = self.client.get("/2024/01/01/algo-que-no-existe/")
        self.assertRedirects(resp, "/blog/", status_code=301, fetch_redirect_response=False)


class StructuredDataTests(TestCase):
    def _ld(self, html):
        import json
        import re

        return [json.loads(m) for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]

    def test_plan_has_offer_in_clf_and_breadcrumbs(self):
        from .models import Plan

        plan = Plan.objects.create(name="Plan Prueba", slug="plan-prueba", currency="UF", price_annual=60, is_active=True)
        data = self._ld(self.client.get(plan.get_absolute_url()).content.decode())
        types = {d["@type"] for d in data}
        self.assertIn("BreadcrumbList", types)
        service = next(d for d in data if d["@type"] == "Service")
        self.assertEqual(service["offers"]["priceCurrency"], "CLF")
        self.assertFalse(service["offers"]["priceSpecification"]["valueAddedTaxIncluded"])

    def test_faq_page_schema_matches_visible_faqs(self):
        FAQ.objects.create(question="¿Pregunta?", answer="<p>Respuesta</p>", is_active=True)
        data = self._ld(self.client.get(reverse("core:faq")).content.decode())
        faq = next(d for d in data if d["@type"] == "FAQPage")
        self.assertEqual(faq["mainEntity"][0]["acceptedAnswer"]["text"], "Respuesta")

    def test_service_and_area_pages_have_service_schema(self):
        from .models import PracticeArea, Service

        area = PracticeArea.objects.create(name="Laboral", slug="laboral", short_description="x", is_active=True)
        service = Service.objects.create(name="Contratos", slug="contratos", short_description="y", area=area, is_active=True)
        for url in (area.get_absolute_url(), service.get_absolute_url()):
            data = self._ld(self.client.get(url).content.decode())
            self.assertIn("Service", {d["@type"] for d in data}, url)
            crumbs = next(d for d in data if d["@type"] == "BreadcrumbList")
            self.assertTrue(crumbs["itemListElement"][-1]["item"].endswith(url))
