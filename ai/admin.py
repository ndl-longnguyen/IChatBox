from django.contrib import admin

from ai.models import (
    AISettings,
    KnowledgeBase,
    KnowledgeChunk,
    KnowledgeDocument,
    TrainingJob,
)


@admin.register(AISettings)
class AISettingsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "auto_reply_enabled",
        "model_name",
        "language",
        "updated_at",
    )
    list_filter = ("auto_reply_enabled", "language", "updated_at")
    search_fields = ("user__username", "model_name")


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
        "source",
        "language",
        "created_at",
    )
    list_filter = ("status", "source", "language", "created_at")
    search_fields = ("title", "content")


@admin.register(KnowledgeChunk)
class KnowledgeChunkAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "document",
        "chunk_index",
        "content_hash",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("content", "document__title")


@admin.register(TrainingJob)
class TrainingJobAdmin(admin.ModelAdmin):
    list_display = ("id", "knowledge_base", "status", "created_at")
    list_filter = ("status", "created_at")
