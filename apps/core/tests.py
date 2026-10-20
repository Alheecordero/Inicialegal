from django.test import TestCase, override_settings
from django.urls import reverse

from .models import FAQ


@override_settings(ALLOWED_HOSTS=["testserver"])
class CorePageTests(TestCase):
    def test_faq_page_renders(self):
        FAQ.objects.create(question="¿La primera reunión tiene costo?", answer="No tiene costo inicial.")

        response = self.client.get(reverse("core:faq"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Preguntas frecuentes")
