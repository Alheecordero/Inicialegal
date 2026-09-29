# inicialegal.cl

Sitio web de **Inicia Legal**: Django 5 (backend, blog y administración de contenido) + plantillas Django con Bootstrap 5 (frontend responsive).

Todo el contenido visible es editable desde el panel de administración: portada, textos, áreas de práctica, servicios, planes, equipo, testimonios, cifras, preguntas frecuentes, páginas legales, blog, comentarios, mensajes de contacto y suscriptores.

## Requisitos

- Python 3.10+
- (Producción) PostgreSQL recomendado, aunque funciona con SQLite.

## Puesta en marcha (desarrollo)

```bash
python3 -m venv .venv            # o: python3 -m virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env             # ajustar valores si es necesario
python manage.py migrate
python manage.py seed --admin    # contenido inicial + superusuario admin / admin1234
python manage.py runserver
```

- Sitio: http://127.0.0.1:8000/
- Administración: http://127.0.0.1:8000/admin/ (usuario `admin`, clave `admin1234`; cámbiala de inmediato).

`seed` es idempotente: carga las áreas, servicios, el Plan Legal Advance (con precios, servicios incluidos, beneficios y FAQ), cifras, páginas legales y cuatro artículos de blog basados en la propuesta comercial. Los testimonios de ejemplo se crean **desactivados**; reemplázalos por reales antes de activarlos.

## Estructura

```
config/            settings, urls, wsgi/asgi
apps/core/         sitio: configuración global, áreas, servicios, planes, equipo, testimonios,
                   cifras, FAQ, páginas, contacto, newsletter, sitemaps, comando `seed`
apps/blog/         categorías, etiquetas, artículos (CKEditor 5), comentarios moderados, RSS, sitemap
templates/         base.html, includes/, core/, blog/, 404/500, robots.txt
static/            css/main.css, js/main.js, img/ (logo, logo blanco, favicon)
media/             archivos subidos desde el admin (ignorado por git)
```

## Funcionalidades

- **Portada dinámica**: hero, cifras, áreas, nosotros, servicios, plan destacado, equipo, testimonios, últimos artículos, FAQ y CTA, todo desde la BD.
- **Servicios y áreas de práctica** con detalle, filtros y relaciones cruzadas.
- **Planes** (ej. Plan Legal Advance) con servicios incluidos, beneficios, inversión, FAQ y brochure descargable.
- **Equipo** con perfiles, áreas y artículos del autor.
- **Blog**: editor enriquecido con subida de imágenes, borradores y publicación programada, destacados, búsqueda, categorías, etiquetas, paginación, artículos relacionados, comentarios con moderación y respuestas, compartir en redes, RSS, datos estructurados (JSON-LD) y Open Graph.
- **Contacto**: formulario con preselección de plan/servicio, honeypot anti-spam, guardado en BD con estados de gestión y notificación por email.
- **Newsletter** (AJAX) con exportación CSV desde el admin.
- **Páginas editables** (privacidad, términos, etc.) con opción de aparecer en menú o pie.
- **SEO**: sitemap.xml, robots.txt, canonical, meta por página, Google Analytics configurable.
- **Botón flotante de WhatsApp**, barra de anuncio opcional, mapa embebido opcional.
- Responsive (Bootstrap 5.3), tipografía Playfair Display + Nunito Sans, paleta del logo (dorado / azul marino / crema).

## Variables de entorno (`.env`)

| Variable | Descripción |
|---|---|
| `DEBUG` | `True` en desarrollo, `False` en producción |
| `SECRET_KEY` | Clave secreta larga y aleatoria |
| `ALLOWED_HOSTS` | Dominios separados por coma |
| `CSRF_TRUSTED_ORIGINS` | Orígenes con esquema, ej. `https://inicialegal.cl` |
| `SITE_URL` | URL pública (para sitemap, OG y canonical) |
| `DATABASE_URL` | `sqlite:///db.sqlite3` o `postgres://user:pass@host:5432/db` |
| `EMAIL_URL` | `consolemail://` en desarrollo; `smtp+tls://user:pass@smtp.host:587` en producción |
| `DEFAULT_FROM_EMAIL` | Remitente de los correos |
| `CONTACT_NOTIFY_EMAIL` | Correo que recibe los avisos del formulario |

| `SITE_INDEXING` | `False` mientras esté en desarrollo: `robots.txt` bloquea todo y se envía `X-Robots-Tag: noindex` |

## Despliegue en Hserver3 (65.109.54.17)

El sitio vive en `/var/www/inicialegal` con PostgreSQL local (BD y rol `inicialegal`), gunicorn por socket
(`gunicorn-inicialegal.socket/.service`) y nginx (`/etc/nginx/sites-available/inicialegal`). Cloudflare
(proxy naranja) delante. Todo lo necesario está en `deploy/`:

| Archivo | Uso |
|---|---|
| `deploy/deploy.sh` | Desde tu máquina: `rsync` + actualización (`migrate`, `collectstatic`, reinicio). `--setup` para la primera instalación. |
| `deploy/server_setup.sh` | Instalación inicial en el servidor (BD, `.env`, venv, systemd, nginx, certificado). |
| `deploy/remote_update.sh` | Actualización en el servidor (lo invoca `deploy.sh`). |
| `deploy/install_nginx.sh` | Instala la config de nginx; usa Let's Encrypt si existe, si no un autofirmado temporal. |
| `deploy/issue_cert.sh` | Emite el certificado Let's Encrypt (requiere que Cloudflare apunte solo a este servidor). |
| `deploy/nginx-inicialegal.conf` | vhost: HTTPS, rate limiting, `noindex`, bloqueo de rutas de escaneo. |
| `deploy/nginx-inicialegal-bots.conf` | `map` de User-Agents de bots/crawlers/IA → 403 (quitar o vaciar al salir a producción). |

Publicar cambios:

```bash
./deploy/deploy.sh
```

Credenciales generadas en el servidor (solo root): `/root/.inicialegal-db-pass` y `/root/.inicialegal-admin-pass`.
El correo del formulario usa `consolemail://` (va al journal de gunicorn) hasta configurar `EMAIL_URL` con SMTP.

### Salir de "modo desarrollo"

1. En `/var/www/inicialegal/.env` poner `SITE_INDEXING=True`.
2. Eliminar `/etc/nginx/conf.d/inicialegal-bots.conf` (o dejar solo scrapers) y quitar la cabecera `X-Robots-Tag` del vhost.
3. `./deploy/deploy.sh`.
