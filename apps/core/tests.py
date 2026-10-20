from django.test import TestCase, override_settings
from django.urls import reverse

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
