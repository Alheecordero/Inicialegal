import json

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import AssistantKnowledgeItem
from .services import search_knowledge


@override_settings(
    ASSISTANT_ENABLED=True,
    ASSISTANT_API_URL="",
    ASSISTANT_API_KEY="",
    ASSISTANT_RATE_LIMIT=100,
    ASSISTANT_MAX_INPUT_CHARS=120,
    ASSISTANT_MAX_CONTEXT_ITEMS=3,
    ASSISTANT_LOG_CONVERSATIONS=False,
)
class AssistantTests(TestCase):
    def setUp(self):
        AssistantKnowledgeItem.objects.create(
            source_type="plan",
            source_id=1,
            title="Plan Legal Advance",
            summary="Asesoria legal preventiva para empresas.",
            content="El Plan Legal Advance incluye acompanamiento societario, contractual y laboral para pymes.",
            url="/planes/legal-advance/",
        )
        AssistantKnowledgeItem.objects.create(
            source_type="service",
            source_id=2,
            title="Contratos comerciales",
            summary="Revision y redaccion de contratos.",
            content="Servicio para preparar contratos, terminos y condiciones, y documentos comerciales.",
            url="/servicios/contratos-comerciales/",
        )

    def test_search_knowledge_returns_relevant_items(self):
        results = search_knowledge("Necesito ayuda con contratos para mi pyme")

        self.assertTrue(results)
        self.assertEqual(results[0].title, "Contratos comerciales")

    def test_chat_endpoint_answers_with_disclaimer_and_sources(self):
        response = self.client.post(
            reverse("assistant:chat"),
            data=json.dumps({"message": "Que incluye el Plan Legal Advance?"}),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertIn("no constituye asesoria legal", data["answer"].lower())
        self.assertEqual(data["sources"][0]["title"], "Plan Legal Advance")

    def test_chat_endpoint_rejects_too_long_message(self):
        response = self.client.post(
            reverse("assistant:chat"),
            data=json.dumps({"message": "x" * 121}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])
