import json

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import AssistantConversation, AssistantMessage
from .services import answer_question


def _client_ip(request):
    return request.META.get("HTTP_CF_CONNECTING_IP") or request.META.get("REMOTE_ADDR") or ""


def _rate_limited(request):
    ip = _client_ip(request)
    key = f"il-assistant:{ip or request.session.session_key or 'anon'}"
    count = cache.get(key, 0)
    if count >= settings.ASSISTANT_RATE_LIMIT:
        return True
    cache.set(key, count + 1, 60)
    return False


def _log_exchange(request, user_message, assistant_message):
    if not settings.ASSISTANT_LOG_CONVERSATIONS:
        return
    if not request.session.session_key:
        request.session.create()
    conversation, _ = AssistantConversation.objects.get_or_create(
        session_key=request.session.session_key,
        defaults={
            "ip_address": _client_ip(request) or None,
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:255],
        },
    )
    AssistantMessage.objects.bulk_create([
        AssistantMessage(conversation=conversation, role="user", content=user_message),
        AssistantMessage(conversation=conversation, role="assistant", content=assistant_message),
    ])


def _clean_history(value):
    if not isinstance(value, list):
        return []
    history = []
    for item in value[-6:]:
        if not isinstance(item, dict):
            continue
        role = "assistant" if item.get("role") == "assistant" else "user"
        content = str(item.get("content", "")).strip()
        if content:
            history.append({"role": role, "content": content[:600]})
    return history


def _clean_page_path(value):
    path = str(value or "").strip()
    if not path.startswith("/"):
        return ""
    return path[:220]


@require_POST
def chat(request):
    if not settings.ASSISTANT_ENABLED:
        return JsonResponse({"ok": False, "message": "El asistente no esta disponible en este momento."}, status=503)
    if _rate_limited(request):
        return JsonResponse(
            {"ok": False, "message": "Recibimos muchas consultas seguidas. Intente nuevamente en un minuto."},
            status=429,
        )
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "message": "Solicitud invalida."}, status=400)

    user_message = str(payload.get("message", "")).strip()
    if not user_message:
        return JsonResponse({"ok": False, "message": "Escriba una consulta para continuar."}, status=400)
    if len(user_message) > settings.ASSISTANT_MAX_INPUT_CHARS:
        return JsonResponse(
            {"ok": False, "message": "La consulta es demasiado extensa. Resuma su duda e intentelo nuevamente."},
            status=400,
        )

    data = answer_question(
        user_message,
        history=_clean_history(payload.get("history")),
        page_path=_clean_page_path(payload.get("page_path")),
    )
    _log_exchange(request, user_message, data["answer"])
    return JsonResponse({"ok": True, **data})
