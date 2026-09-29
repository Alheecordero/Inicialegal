from django.contrib import admin
from django.utils.html import format_html

from .models import (
    FAQ,
    ContactMessage,
    NewsletterSubscriber,
    Page,
    Plan,
    PlanBenefit,
    PlanFeature,
    PracticeArea,
    Service,
    SiteSettings,
    HeroSlide,
    Stat,
    TeamMember,
    Testimonial,
)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Identidad", {"fields": ("site_name", "tagline", "logo", "logo_white", "favicon", "announcement", "announcement_url")}),
        ("Contacto", {"fields": ("email", "phone", "whatsapp", "whatsapp_message", "address", "city", "schedule", "map_embed_url")}),
        ("Redes sociales", {"fields": ("instagram", "linkedin", "facebook", "tiktok", "youtube"), "classes": ("collapse",)}),
        ("Portada (hero)", {"fields": ("hero_kicker", "hero_title", "hero_subtitle", "hero_image", "hero_image_mobile", "hero_primary_text", "hero_primary_url", "hero_secondary_text", "hero_secondary_url"), "description": "Se usa solo si el carrusel del inicio no tiene diapositivas activas."}),
        ("Sección Nosotros", {"fields": ("about_kicker", "about_title", "about_text", "about_image")}),
        ("Llamado a la acción", {"fields": ("cta_title", "cta_text", "cta_button_text", "cta_button_url")}),
        ("SEO y pie de página", {"fields": ("meta_description", "meta_keywords", "google_analytics_id", "footer_text", "monogram"), "classes": ("collapse",)}),
        ("Aviso de cookies (Ley 21.719)", {"fields": ("cookie_consent_enabled", "cookie_consent_title", "cookie_consent_text", "cookie_policy_url", "privacy_policy_url"), "classes": ("collapse",)}),
    )

    save_on_top = True

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        from django.shortcuts import redirect
        obj = SiteSettings.load()
        return redirect(f"./{obj.pk}/change/")


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ("order", "key", "title", "variant", "is_active")
    list_editable = ("order", "is_active")
    list_display_links = ("key", "title")
    fields = (
        "key", "variant", "order", "is_active",
        "kicker", "title", "subtitle", "image", "image_mobile",
        "primary_text", "primary_url", "secondary_text", "secondary_url",
    )


@admin.register(PracticeArea)
class PracticeAreaAdmin(admin.ModelAdmin):
    list_display = ("name", "icon_preview", "show_on_home", "is_active", "order")
    list_editable = ("show_on_home", "is_active", "order")
    search_fields = ("name", "short_description")
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="ícono")
    def icon_preview(self, obj):
        return format_html('<i class="bi {}"></i> {}', obj.icon, obj.icon)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "area", "is_featured", "is_active", "order")
    list_editable = ("is_featured", "is_active", "order")
    list_filter = ("area", "is_featured", "is_active")
    search_fields = ("name", "short_description")
    prepopulated_fields = {"slug": ("name",)}


class PlanFeatureInline(admin.TabularInline):
    model = PlanFeature
    extra = 1


class PlanBenefitInline(admin.TabularInline):
    model = PlanBenefit
    extra = 1


class FAQInline(admin.TabularInline):
    model = FAQ
    extra = 0
    fields = ("question", "answer", "order", "is_active")


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price_annual", "installments", "price_installment", "is_featured", "is_active", "order")
    list_editable = ("is_featured", "is_active", "order")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [PlanFeatureInline, PlanBenefitInline, FAQInline]
    save_on_top = True
    fieldsets = (
        (None, {"fields": ("name", "slug", "tagline", "summary", "image", "is_featured", "is_active", "order", "cta_text", "brochure")}),
        ("Contenido", {"fields": ("problem_title", "problem_text", "solution_title", "solution_text", "description")}),
        ("Inversión", {"fields": ("currency", "price_annual", "installments", "price_installment", "price_suffix", "payment_modality", "price_note")}),
        ("Beneficio preferente", {"fields": ("discount_badge", "discount_text")}),
    )


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "specialty", "show_on_home", "is_active", "order")
    list_editable = ("show_on_home", "is_active", "order")
    search_fields = ("name", "role", "specialty")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("areas",)


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("client_name", "company", "rating", "is_active", "order")
    list_editable = ("is_active", "order")


@admin.register(Stat)
class StatAdmin(admin.ModelAdmin):
    list_display = ("value", "label", "is_active", "order")
    list_editable = ("is_active", "order")


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "plan", "is_active", "order")
    list_editable = ("is_active", "order")
    list_filter = ("plan",)
    search_fields = ("question", "answer")


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "show_in_footer", "show_in_menu", "order")
    list_editable = ("is_published", "show_in_footer", "show_in_menu", "order")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "plan", "status_badge", "privacy_accepted", "created_at")
    list_filter = ("status", "plan", "service", "created_at")
    search_fields = ("name", "email", "company", "message")
    readonly_fields = ("name", "email", "phone", "company", "subject", "message", "plan", "service", "source", "privacy_accepted", "created_at")
    date_hierarchy = "created_at"
    actions = ("mark_in_progress", "mark_closed")
    fieldsets = (
        ("Seguimiento", {"fields": ("status", "internal_notes")}),
        ("Solicitud", {"fields": ("name", "email", "phone", "company", "plan", "service", "subject", "message", "privacy_accepted", "source", "created_at")}),
    )

    @admin.display(description="estado", ordering="status")
    def status_badge(self, obj):
        label = dict(ContactMessage.STATUS).get(obj.status, obj.status)
        return format_html('<span class="il-badge il-badge-{}">{}</span>', obj.status, label)

    @admin.action(description="Marcar como en gestión")
    def mark_in_progress(self, request, queryset):
        queryset.update(status="in_progress")

    @admin.action(description="Marcar como cerradas")
    def mark_closed(self, request, queryset):
        queryset.update(status="closed")

    def has_add_permission(self, request):
        return False


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "is_active", "privacy_accepted", "created_at")
    list_filter = ("is_active",)
    search_fields = ("email", "name")
    actions = ["export_csv"]

    @admin.action(description="Exportar seleccionados a CSV")
    def export_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="suscriptores.csv"'
        writer = csv.writer(response)
        writer.writerow(["email", "nombre", "activo", "acepto_publicaciones", "fecha"])
        for s in queryset:
            writer.writerow([s.email, s.name, s.is_active, s.privacy_accepted, s.created_at.strftime("%Y-%m-%d")])
        return response
