from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Page, Plan, PracticeArea, Service


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return ["core:home", "core:about", "core:service_list", "core:plan_list", "core:team_list", "core:faq", "core:contact", "blog:post_list"]

    def location(self, item):
        return reverse(item)


class ServiceSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Service.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class PracticeAreaSitemap(ServiceSitemap):
    def items(self):
        return PracticeArea.objects.filter(is_active=True)


class PlanSitemap(ServiceSitemap):
    priority = 0.9

    def items(self):
        return Plan.objects.filter(is_active=True)


class PageSitemap(ServiceSitemap):
    priority = 0.4

    def items(self):
        return Page.objects.filter(is_published=True)
