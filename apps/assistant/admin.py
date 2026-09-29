from django.contrib import admin

from .models import AssistantConversation, AssistantKnowledgeItem, AssistantMessage


@admin.register(AssistantKnowledgeItem)
class AssistantKnowledgeItemAdmin(admin.ModelAdmin):
    list_display = ("title", "source_type", "is_active", "updated_at")
    list_filter = ("source_type", "is_active")
    search_fields = ("title", "summary", "content")
    readonly_fields = ("source_type", "source_id", "source_updated_at", "created_at", "updated_at")


class AssistantMessageInline(admin.TabularInline):
    model = AssistantMessage
    extra = 0
    readonly_fields = ("role", "content", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AssistantConversation)
class AssistantConversationAdmin(admin.ModelAdmin):
    list_display = ("session_key", "ip_address", "created_at", "updated_at")
    search_fields = ("session_key", "ip_address", "messages__content")
    readonly_fields = ("session_key", "ip_address", "user_agent", "created_at", "updated_at")
    inlines = [AssistantMessageInline]

    def has_add_permission(self, request):
        return False
