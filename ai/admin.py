from django.contrib import admin

from ai.models import KnowledgeBase, KnowledgeDocument, TrainingJob


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "name", "language", "is_active", "created_at")
    list_filter = ("is_active", "language", "created_at")
    search_fields = ("name", "user__username")


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "knowledge_base",
        "title",
        "status",
        "language",
        "created_at",
    )
    list_filter = ("status", "language", "created_at")
    search_fields = ("title", "content")


@admin.register(TrainingJob)
class TrainingJobAdmin(admin.ModelAdmin):
    list_display = ("id", "knowledge_base", "status", "created_at")
    list_filter = ("status", "created_at")
