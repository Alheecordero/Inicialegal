from django.conf import settings

from .forms import NewsletterForm
from .models import Page, Plan, PracticeArea, Service, SiteSettings


def site_context(request):
    path = request.path or "/"
    query = request.META.get("QUERY_STRING", "")
    canonical = path + (f"?{query}" if query else "")
    return {
        "site": SiteSettings.load(),
        "site_url": settings.SITE_URL,
        "site_indexing": settings.SITE_INDEXING,
        "canonical_path": canonical,
        "nav_areas": PracticeArea.objects.filter(is_active=True).only("name", "slug"),
        "nav_services": Service.objects.filter(is_active=True).only("name", "slug")[:8],
        "nav_plans": Plan.objects.filter(is_active=True).only("name", "slug"),
        "menu_pages": Page.objects.filter(is_published=True, show_in_menu=True).only("title", "slug"),
        "footer_pages": Page.objects.filter(is_published=True, show_in_footer=True).only("title", "slug"),
        "newsletter_form": NewsletterForm(),
    }
