from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Comment, Post, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "color_preview", "published_count", "order")
    list_editable = ("order",)
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="color")
    def color_preview(self, obj):
        return format_html('<span style="display:inline-block;width:16px;height:16px;border-radius:50%;background:{};vertical-align:middle"></span> {}', obj.color, obj.color)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ("name", "email", "body", "is_approved", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author_name", "status", "published_at", "is_featured", "views")
    list_filter = ("status", "is_featured", "category", "published_at")
    list_editable = ("status", "is_featured")
    search_fields = ("title", "excerpt", "content")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags", "areas")
    date_hierarchy = "published_at"
    autocomplete_fields = ("author",)
    inlines = [CommentInline]
    save_on_top = True
    fieldsets = (
        (None, {"fields": ("title", "slug", "status", "published_at", "is_featured", "allow_comments")}),
        ("Contenido", {"fields": ("cover_image", "cover_caption", "excerpt", "content")}),
        ("Clasificación", {"fields": ("category", "tags", "areas", "author", "author_display")}),
        ("SEO", {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)}),
    )

    def get_changeform_initial_data(self, request):
        return {"author": request.user}

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "post", "is_approved", "created_at")
    list_filter = ("is_approved", "created_at")
    list_editable = ("is_approved",)
    search_fields = ("name", "email", "body")
    actions = ["approve"]

    @admin.action(description="Aprobar comentarios seleccionados")
    def approve(self, request, queryset):
        queryset.update(is_approved=True)
