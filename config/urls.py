from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from apps.blog.feeds import LatestPostsFeed
from apps.blog.sitemaps import PostSitemap
from apps.core.sitemaps import (
    PageSitemap,
    PlanSitemap,
    PracticeAreaSitemap,
    ServiceSitemap,
    StaticViewSitemap,
    TeamSitemap,
)

sitemaps = {
    "static": StaticViewSitemap,
    "servicios": ServiceSitemap,
    "areas": PracticeAreaSitemap,
    "planes": PlanSitemap,
    "paginas": PageSitemap,
    "equipo": TeamSitemap,
    "blog": PostSitemap,
}

urlpatterns = [
    path(settings.ADMIN_PATH, admin.site.urls),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path("blog/feed/", LatestPostsFeed(), name="blog_feed"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots",
    ),
    path(
        "googlef65bbc244d1047fc.html",
        TemplateView.as_view(template_name="googlef65bbc244d1047fc.html", content_type="text/html"),
    ),
    path(
        "BingSiteAuth.xml",
        TemplateView.as_view(template_name="BingSiteAuth.xml", content_type="application/xml"),
    ),
    path("asistente/", include("apps.assistant.urls", namespace="assistant")),
    path("blog/", include("apps.blog.urls", namespace="blog")),
    path("", include("apps.core.urls", namespace="core")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"

admin.site.site_header = "Inicia Legal"
admin.site.site_title = "Inicia Legal"
admin.site.index_title = "Panel"
admin.site.empty_value_display = "—"
