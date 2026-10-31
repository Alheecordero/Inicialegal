from django.core.cache import cache


def client_ip(request):
    """IP del visitante.

    nginx resuelve la IP real a partir de CF-Connecting-IP (solo para conexiones de Cloudflare)
    y la reenvía en X-Real-IP, pisando lo que mande el cliente. Leer CF-Connecting-IP aquí
    dejaría falsificarla a quien llegue al origen sin pasar por Cloudflare.
    """
    return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR") or ""


def hit(key, limit, window):
    """Suma un intento a `key` y responde True si ya superó `limit` dentro de `window` segundos."""
    key = "il-rl:" + key
    cache.add(key, 0, window)
    try:
        count = cache.incr(key)
    except ValueError:  # expiró entre add e incr
        cache.set(key, 1, window)
        count = 1
    return count > limit


def peek(key):
    return cache.get("il-rl:" + key, 0)


def reset(key):
    cache.delete("il-rl:" + key)
