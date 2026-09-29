from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Sitio"

    def ready(self):
        from django.contrib import admin

        if getattr(admin.site, "_il_panel", False):
            return
        admin.site._il_panel = True
        original_apps = admin.site.get_app_list
        original_index = admin.site.index
        business_models = ("contactmessage", "newslettersubscriber")
        editing_order = [
            "sitesettings", "heroslide", "practicearea", "service", "plan",
            "teammember", "page", "faq", "testimonial", "stat",
            "post", "comment", "category", "tag",
        ]

        def _rank(names, model):
            name = model["model"]._meta.model_name
            return names.index(name) if name in names else 100

        def get_app_list(request, app_label=None):
            apps = original_apps(request, None if app_label in ("negocio", "edicion") else app_label)
            core = next((app for app in apps if app["app_label"] == "core"), None)
            blog = next((app for app in apps if app["app_label"] == "blog"), None)
            rest = [app for app in apps if app["app_label"] not in ("core", "blog")]
            grouped = []
            if core and app_label in (None, "core", "negocio", "edicion"):
                business = [model for model in core["models"] if model["model"]._meta.model_name in business_models]
                editing = [model for model in core["models"] if model["model"]._meta.model_name not in business_models]
                if blog and app_label in (None, "edicion"):
                    editing.extend(blog["models"])
                business.sort(key=lambda model: _rank(business_models, model))
                editing.sort(key=lambda model: _rank(editing_order, model))
                if business and app_label in (None, "core", "negocio"):
                    grouped.append({
                        **core,
                        "name": "Negocio",
                        "app_label": "negocio",
                        "app_url": business[0]["admin_url"],
                        "models": business,
                    })
                if editing and app_label in (None, "core", "edicion"):
                    grouped.append({
                        **core,
                        "name": "Edición del sitio",
                        "app_label": "edicion",
                        "app_url": editing[0]["admin_url"],
                        "models": editing,
                    })
            elif blog and app_label == "blog":
                grouped.append(blog)
            if app_label is None:
                for app in rest:
                    if app["app_label"] == "auth":
                        app["name"] = "Acceso"
                grouped.extend(rest)
            elif not grouped:
                grouped = apps
            return grouped

        def index(request, extra_context=None):
            from apps.blog.models import Post
            from apps.core.models import ContactMessage, NewsletterSubscriber

            extra = dict(extra_context or {})
            extra["il_new_messages"] = ContactMessage.objects.filter(status="new").count()
            extra["il_recent_messages"] = list(
                ContactMessage.objects.select_related("plan").order_by("-created_at")[:6]
            )
            extra["il_subscribers"] = NewsletterSubscriber.objects.filter(is_active=True).count()
            extra["il_posts"] = Post.objects.filter(status=Post.PUBLISHED).count()
            return original_index(request, extra)

        admin.site.get_app_list = get_app_list
        admin.site.index = index
