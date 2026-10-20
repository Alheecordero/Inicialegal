import json
import re
import unicodedata
from collections import Counter
from urllib import error, request
from urllib.parse import urlparse

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
CONTACT_TERMS = {"agendar", "agenda", "reunion", "reunirse", "contactar", "contacto", "whatsapp", "telefono", "llamar"}
HIGH_RISK_TERMS = {"demandar", "demanda", "despedir", "despido", "juicio", "querella", "denuncia", "sii", "multa"}
SERVICE_TERMS = {"contrato", "contratos", "marca", "marcas", "laboral", "tributario", "compliance", "datos", "sociedad", "societario"}
PRICE_TERMS = {"precio", "valor", "cuanto", "cuota", "inversion", "pago", "uf"}
INCLUSION_TERMS = {"incluye", "incluido", "incluidos", "servicios", "beneficios"}


def clean_html(value):
    text = strip_tags(value or "")
    return re.sub(r"\s+", " ", text).strip()


def normalize_text(value):
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.lower()


def tokenize(value):
    words = re.findall(r"[a-z0-9]{3,}", normalize_text(value))
    tokens = []
    for word in words:
        if word in STOPWORDS:
            continue
        tokens.append(word)
        if word.endswith("s") and len(word) > 4:
            tokens.append(word[:-1])
    return tokens


def query_intent(query):
    terms = set(tokenize(query))
    if terms & CONTACT_TERMS:
        return "contact"
    if terms & HIGH_RISK_TERMS:
        return "high_risk"
    return "general"


def normalize_path(value):
    path = urlparse(value or "").path or ""
    if not path.startswith("/"):
        path = f"/{path}"
    return path.rstrip("/") or "/"


def search_knowledge(query, limit=None, page_path=""):
    limit = limit or settings.ASSISTANT_MAX_CONTEXT_ITEMS
    query_terms = Counter(tokenize(query))
    if not query_terms:
        return []
    ranked = []
    current_path = normalize_path(page_path)
    explicit_plan_terms = {"advance", "pyme"} & set(query_terms)
    items = AssistantKnowledgeItem.objects.filter(is_active=True).only(
        "source_type", "title", "summary", "content", "url"
    )
    for item in items:
        title_terms = set(tokenize(item.title))
        item_path = normalize_path(item.url)
        terms = Counter(tokenize(f"{item.title} {item.summary} {item.content}"))
        score = sum(min(count, terms.get(term, 0)) for term, count in query_terms.items())
        page_context_allowed = not explicit_plan_terms or bool(title_terms & explicit_plan_terms)
        if page_context_allowed and current_path != "/" and item_path == current_path:
            score += 10
        elif page_context_allowed and current_path != "/" and item_path.startswith(current_path):
            score += 5
        if item.source_type == "service" and set(query_terms) & SERVICE_TERMS:
            score += 4
        if item.source_type == "plan" and {"plan", "advance", "pyme"} & set(query_terms):
            score += 4
        if item.source_type == "faq" and "incluye" in set(query_terms) and "incluye" in title_terms:
            score += 8
        if item.source_type == "plan" and set(query_terms) & PRICE_TERMS:
            score += 5
        if item.source_type in {"plan", "faq"} and set(query_terms) & INCLUSION_TERMS:
            score += 3
        if title_terms & set(query_terms):
            score += 3
        if score:
            title_hits = sum(2 for term in query_terms if term in title_terms)
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


def build_system_prompt(page_path=""):
    contact_url = reverse("core:contact")
    page_note = f" La consulta viene desde la ruta {page_path}." if page_path else ""
    return (
        "Eres el asistente de Inicia Legal, estudio juridico para empresas en Chile. "
        "Responde en espanol de Chile, con tono claro, prudente y profesional. "
        "Usa solo el contexto entregado y el contenido publico del sitio. "
        "Cuando la consulta sea ambigua, prioriza el contenido de la pagina actual y menciona que puedes derivar a reunion. "
        "No inventes precios, plazos, resultados ni normas especificas si no aparecen en el contexto. "
        "No entregues estrategia legal personalizada ni conclusiones vinculantes. "
        "Si la pregunta requiere revisar antecedentes concretos, deriva a contacto o WhatsApp. "
        f"Incluye siempre una advertencia breve: {LEGAL_DISCLAIMER} "
        f"URL de contacto: {contact_url}.{page_note}"
    )


def build_messages(user_message, context_items, history=None, page_path=""):
    context = "\n\n".join(
        f"Fuente: {item.title}\nTipo: {item.get_source_type_display()}\nURL: {item.url}\nContenido: {item.content[:1600]}"
        for item in context_items
    ) or "No hay contexto coincidente en el sitio."
    safe_history = []
    for msg in (history or [])[-6:]:
        role = "assistant" if msg.get("role") == "assistant" else "user"
        content = str(msg.get("content", ""))[:600].strip()
        if content:
            safe_history.append({"role": role, "content": content})
    return [
        {"role": "system", "content": build_system_prompt(page_path=page_path)},
        *safe_history,
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
    return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()


def fallback_answer(context_items):
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


def plan_answer(context_items):
    plan = next((item for item in context_items if item.source_type == "plan"), None)
    if not plan:
        return None
    related_faqs = [item for item in context_items if item.source_type == "faq" and item.url == plan.url][:2]
    price_match = re.search(r"Valor anual:[^\n]+", plan.content or "")
    details = [f"Base principal: {plan.title}. {(plan.summary or plan.content)[:360].strip()}"]
    if price_match:
        details.append(price_match.group(0).strip())
    details.extend(f"{faq.title}: {(faq.summary or faq.content)[:260].strip()}" for faq in related_faqs)
    return {
        "answer": (
            f"{LEGAL_DISCLAIMER}\n\n"
            + "\n".join(f"- {line}" for line in details)
            + f"\n\nPuede revisar el detalle del plan en: {plan.url}\n\n{DERIVATION_TEXT}"
        ),
        "sources": source_payload(context_items),
        "contact_url": reverse("core:contact"),
    }


def contact_answer(context_items):
    return {
        "answer": (
            f"{LEGAL_DISCLAIMER}\n\n"
            "Puede solicitar una reunion desde el formulario de contacto o escribir por WhatsApp. "
            "La reunion inicial no tiene costo y permite conocer la situacion juridica de la empresa.\n\n"
            f"{DERIVATION_TEXT}"
        ),
        "sources": source_payload(context_items),
        "contact_url": reverse("core:contact"),
    }


def high_risk_answer(context_items):
    return {
        "answer": (
            f"{LEGAL_DISCLAIMER}\n\n"
            "Para una decision como demandar, despedir, responder una denuncia, enfrentar una multa o iniciar un juicio, "
            "no corresponde dar una instruccion general sin revisar antecedentes, documentos y plazos. "
            "Lo prudente es agendar una reunion para que el equipo evalúe el caso concreto.\n\n"
            f"{DERIVATION_TEXT}"
        ),
        "sources": source_payload(context_items),
        "contact_url": reverse("core:contact"),
    }


def service_answer(context_items):
    service_items = [item for item in context_items if item.source_type == "service"][:3]
    if not service_items:
        return None
    lines = "\n".join(f"- {item.title}: {item.url}" for item in service_items)
    return {
        "answer": (
            f"{LEGAL_DISCLAIMER}\n\n"
            "Encontré servicios relacionados con su consulta:\n"
            f"{lines}\n\n"
            "Para saber cuál aplica mejor, conviene revisar el tipo de contrato, contraparte, riesgos y documentos disponibles. "
            f"{DERIVATION_TEXT}"
        ),
        "sources": source_payload(context_items),
        "contact_url": reverse("core:contact"),
    }


def ensure_disclaimer(answer):
    if "no constituye asesoria legal" in normalize_text(answer):
        return answer
    return f"{LEGAL_DISCLAIMER}\n\n{answer}"


def search_query(user_message, history=None):
    if {"advance", "pyme"} & set(tokenize(user_message)):
        return user_message
    recent_user_context = " ".join(
        str(msg.get("content", ""))[:180]
        for msg in (history or [])[-4:]
        if msg.get("role") == "user"
    )
    return f"{recent_user_context} {user_message}".strip()


def answer_question(user_message, history=None, page_path=""):
    context_items = search_knowledge(search_query(user_message, history=history), page_path=page_path)
    intent = query_intent(user_message)
    if intent == "contact":
        return contact_answer(context_items)
    if intent == "high_risk":
        return high_risk_answer(context_items)
    if set(tokenize(user_message)) & SERVICE_TERMS:
        service_response = service_answer(context_items)
        if service_response:
            return service_response
    if set(tokenize(user_message)) & (PRICE_TERMS | INCLUSION_TERMS | {"plan", "pyme", "advance"}):
        plan_response = plan_answer(context_items)
        if plan_response:
            return plan_response
    messages = build_messages(user_message, context_items, history=history, page_path=page_path)
    answer = ensure_disclaimer(call_llm(messages) or fallback_answer(context_items))
    return {
        "answer": answer,
        "sources": source_payload(context_items),
        "contact_url": reverse("core:contact"),
    }
