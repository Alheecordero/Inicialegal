"""
Configuración Django para inicialegal.cl
"""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CSRF_TRUSTED_ORIGINS=(list, []),
    SECRET_KEY=(str, "cambia-esta-clave-en-produccion"),
    DATABASE_URL=(str, f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
    EMAIL_URL=(str, "consolemail://"),
    DEFAULT_FROM_EMAIL=(str, "Inicia Legal <formularios@inicialegal.cl>"),
    CONTACT_NOTIFY_EMAIL=(str, "contacto@inicialegal.cl"),
    SITE_URL=(str, "http://127.0.0.1:8000"),
    SITE_INDEXING=(bool, True),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")
SITE_URL = env("SITE_URL")
# False mientras el sitio está en desarrollo: robots.txt bloquea todo y se envía X-Robots-Tag: noindex
SITE_INDEXING = env("SITE_INDEXING")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
    "django_ckeditor_5",
    "apps.core",
    "apps.blog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "apps.core.middleware.SiteLocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.core.middleware.AdminLoginThrottleMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.NoIndexMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.i18n",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {"default": env.db("DATABASE_URL")}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-cl"
LANGUAGES = [
    ("es-cl", "Español"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        if not DEBUG
        else "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email
email_config = env.email_url("EMAIL_URL")
vars().update(email_config)
if email_config.get("EMAIL_HOST") == "smtp-relay.gmail.com":
    EMAIL_BACKEND = "apps.core.mail.GoogleRelayBackend"
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")
CONTACT_NOTIFY_EMAIL = env("CONTACT_NOTIFY_EMAIL")
CONTACT_CLIENT_FROM_EMAIL = env(
    "CONTACT_CLIENT_FROM_EMAIL",
    default=f"Inicia Legal <{env('CONTACT_NOTIFY_EMAIL')}>",
)

# Ruta del panel. No usar /admin/: es la dirección que prueban los escáneres.
ADMIN_PATH = "gestion/"

# Seguridad en producción
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Paginación blog
BLOG_PAGINATE_BY = 6

# CKEditor 5
CKEDITOR_5_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
CKEDITOR_5_UPLOAD_FILE_TYPES = ["jpeg", "jpg", "png", "gif", "webp", "pdf"]
CKEDITOR_5_CONFIGS = {
    "default": {
        "language": "es",
        "toolbar": [
            "heading", "|", "bold", "italic", "underline", "link", "|",
            "bulletedList", "numberedList", "blockQuote", "|",
            "insertTable", "imageUpload", "mediaEmbed", "|", "undo", "redo",
        ],
        "heading": {
            "options": [
                {"model": "paragraph", "title": "Párrafo", "class": "ck-heading_paragraph"},
                {"model": "heading2", "view": "h2", "title": "Título 2", "class": "ck-heading_heading2"},
                {"model": "heading3", "view": "h3", "title": "Título 3", "class": "ck-heading_heading3"},
                {"model": "heading4", "view": "h4", "title": "Título 4", "class": "ck-heading_heading4"},
            ]
        },
        "image": {
            "toolbar": ["imageTextAlternative", "|", "imageStyle:alignLeft", "imageStyle:full", "imageStyle:alignRight"],
            "styles": ["full", "alignLeft", "alignRight"],
        },
        "table": {"contentToolbar": ["tableColumn", "tableRow", "mergeTableCells"]},
    },
}
