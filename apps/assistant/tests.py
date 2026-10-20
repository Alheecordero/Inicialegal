import json

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import AssistantKnowledgeItem
from .services import answer_question, search_knowledge


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

    def test_answer_uses_page_context_for_ambiguous_plan_question(self):
        AssistantKnowledgeItem.objects.create(
            source_type="plan",
            source_id=3,
            title="Plan Legal Pyme",
            summary="Plan anual para pymes.",
            content="Incluye 2 contratos anuales, auditorias laborales y revision mensual de contratos.",
            url="/planes/plan-legal-pyme/",
        )

        data = answer_question("¿Qué incluye?", page_path="/planes/plan-legal-pyme/")

        self.assertEqual(data["sources"][0]["title"], "Plan Legal Pyme")
        self.assertIn("Plan Legal Pyme", data["answer"])

    def test_chat_endpoint_accepts_history_and_page_path(self):
        response = self.client.post(
            reverse("assistant:chat"),
            data=json.dumps({
                "message": "¿Y cuánto cuesta?",
                "history": [{"role": "user", "content": "Me interesa el Plan Legal Advance"}],
                "page_path": "/planes/legal-advance/",
            }),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])

    def test_current_plan_name_overrides_page_context(self):
        AssistantKnowledgeItem.objects.create(
            source_type="plan",
            source_id=3,
            title="Plan Legal Pyme",
            summary="Plan anual para pymes.",
            content="Valor anual: UF 60 + IVA.",
            url="/planes/plan-legal-pyme/",
        )

        data = answer_question(
            "¿Y el Advance?",
            history=[{"role": "user", "content": "Estoy viendo planes para mi pyme"}],
            page_path="/planes/plan-legal-pyme/",
        )

        self.assertEqual(data["sources"][0]["title"], "Plan Legal Advance")
