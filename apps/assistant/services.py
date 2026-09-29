import json
import re
import unicodedata
from collections import Counter
from urllib import error, request

from django.conf import settings
from django.urls import reverse
from django.utils.html import strip_tags

from .models import AssistantKnowledgeItem


LEGAL_DISCLAIMER = (
    "Puedo orientarle con informacion general de Inicia Legal. "
    "Esto no constituye asesoria legal ni crea una relacion abogado-cliente."
)

DERIVATION_TEXT = (
    "Si su caso requiere revisar documentos, plazos, contratos o antecedentes concretos, "
    "le recomiendo solicitar una reunion con el equipo."
)

STOPWORDS = {
    "a", "al", "ante", "bajo", "con", "contra", "de", "del", "desde", "e", "el", "en",
    "entre", "es", "esa", "ese", "esta", "este", "esto", "la", "las", "le", "lo", "los",
    "mi", "no", "o", "para", "por", "que", "se", "si", "sin", "sobre", "su", "sus", "un",
    "una", "y", "ya", "como", "cual", "cuando", "donde", "empresa", "legal",
}


def clean_html(value):
    text = strip_tags(value or "")
    return re.sub(r"\s+", " ", text).strip()


def normalize_text(value):
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.lower()


def tokenize(value):
    words = re.findall(r"[a-z0-9]{3,}", normalize_text(value))
    return [word for word in words if word not in STOPWORDS]


def search_knowledge(query, limit=None):
    limit = limit or settings.ASSISTANT_MAX_CONTEXT_ITEMS
    query_terms = Counter(tokenize(query))
    if not query_terms:
        return []

    ranked = []
    items = AssistantKnowledgeItem.objects.filter(is_active=True).only(
        "id", "source_type", "title", "summary", "content", "url"
    )
    for item in items:
        haystack = f"{item.title} {item.summary} {item.content}"
        terms = Counter(tokenize(haystack))
        score = sum(min(count, terms.get(term, 0)) for term, count in query_terms.items())
        if score:
            title_hits = sum(2 for term in query_terms if term in tokenize(item.title))
            ranked.append((score + title_hits, item))

    ranked.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in ranked[:limit]]


def source_payload(items):
    return [
        {
            "title": item.title,
            "type": item.get_source_type_display(),
            "url": item.url,
            "excerpt": (item.summary or item.content)[:260],
        }
        for item in items
    ]


def build_system_prompt():
    contact_url = reverse("core:contact")
    return (
        "Eres el asistente de Inicia Legal, estudio juridico para empresas en Chile. "
        "Responde en espanol de Chile, con tono claro, prudente y profesional. "
        "Usa solo el contexto entregado y el contenido publico del sitio. "
        "No inventes precios, plazos, resultados ni normas especificas si no aparecen en el contexto. "
        "No entregues estrategia legal personalizada ni conclusiones vinculantes. "
        "Si la pregunta requiere revisar antecedentes concretos, deriva a contacto o WhatsApp. "
        f"Incluye siempre una advertencia breve: {LEGAL_DISCLAIMER} "
        f"URL de contacto: {contact_url}"
    )


def build_messages(user_message, context_items):
    context = "\n\n".join(
        f"Fuente: {item.title}\nTipo: {item.get_source_type_display()}\nURL: {item.url}\nContenido: {item.content[:1600]}"
        for item in context_items
    ) or "No hay contexto coincidente en el sitio."
    return [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": f"Contexto disponible:\n{context}\n\nPregunta del visitante:\n{user_message}"},
    ]


def call_llm(messages):
    if not settings.ASSISTANT_API_URL or not settings.ASSISTANT_API_KEY:
        return ""

    payload = json.dumps({
        "model": settings.ASSISTANT_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 550,
    }).encode("utf-8")
    req = request.Request(
        settings.ASSISTANT_API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.ASSISTANT_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=settings.ASSISTANT_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (error.URLError, TimeoutError, ValueError, KeyError):
        return ""

    return (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
    )


def fallback_answer(user_message, context_items):
    if not context_items:
        return (
            f"{LEGAL_DISCLAIMER}\n\n"
            "No encontre una respuesta suficientemente clara en el contenido publicado del sitio. "
            f"{DERIVATION_TEXT}"
        )

    first = context_items[0]
    excerpt = (first.summary or first.content)[:520].strip()
    link = f"\n\nPuede revisar mas detalle en: {first.url}" if first.url else ""
    return (
        f"{LEGAL_DISCLAIMER}\n\n"
        f"Segun la informacion publicada sobre {first.title}, {excerpt}{link}\n\n"
        f"{DERIVATION_TEXT}"
    )


def ensure_disclaimer(answer):
    normalized = normalize_text(answer)
    if "no constituye asesoria legal" in normalized:
        return answer
    return f"{LEGAL_DISCLAIMER}\n\n{answer}"


def answer_question(user_message):
    context_items = search_knowledge(user_message)
    messages = build_messages(user_message, context_items)
    answer = ensure_disclaimer(call_llm(messages) or fallback_answer(user_message, context_items))
    return {
        "answer": answer,
        "sources": source_payload(context_items),
        "contact_url": reverse("core:contact"),
    }
