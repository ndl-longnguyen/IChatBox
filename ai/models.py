from django.conf import settings
from django.db import models


class AISettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_settings",
    )
    auto_reply_enabled = models.BooleanField(default=False)
    model_name = models.CharField(max_length=100, blank=True, default="")
    language = models.CharField(max_length=10, default="vi")
    system_prompt = models.TextField(
        default=(
            "You are a helpful website support assistant. Answer only from "
            "the provided business knowledge. If the answer is not in the "
            "knowledge, say you do not have enough information and ask the "
            "visitor to wait for a human agent."
        )
    )
    max_context_chunks = models.PositiveSmallIntegerField(default=6)
    temperature = models.FloatField(default=0.2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AI settings for {self.user}"


class KnowledgeBase(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="knowledge_bases",
    )
    name = models.CharField(max_length=255, default="Default")
    language = models.CharField(max_length=10, default="en")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class KnowledgeDocument(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "DRAFT"),
        ("READY", "READY"),
        ("ARCHIVED", "ARCHIVED"),
    ]

    knowledge_base = models.ForeignKey(
        KnowledgeBase, on_delete=models.CASCADE, related_name="documents"
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    content_hash = models.CharField(max_length=64, blank=True, default="")
    source = models.CharField(max_length=50, default="manual")
    source_file = models.FileField(
        upload_to="ai_knowledge/",
        null=True,
        blank=True,
    )
    language = models.CharField(max_length=10, default="en")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="DRAFT"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "language"]),
            models.Index(fields=["source", "created_at"]),
        ]

    def __str__(self):
        return self.title


class KnowledgeChunk(models.Model):
    document = models.ForeignKey(
        KnowledgeDocument, on_delete=models.CASCADE, related_name="chunks"
    )
    chunk_index = models.PositiveIntegerField()
    content = models.TextField()
    content_hash = models.CharField(max_length=64, db_index=True)
    char_start = models.PositiveIntegerField(default=0)
    char_end = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["document_id", "chunk_index"]
        unique_together = ("document", "chunk_index")
        indexes = [
            models.Index(fields=["document", "chunk_index"]),
        ]

    def __str__(self):
        return f"{self.document_id}#{self.chunk_index}"


class TrainingJob(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "PENDING"),
        ("RUNNING", "RUNNING"),
        ("SUCCEEDED", "SUCCEEDED"),
        ("FAILED", "FAILED"),
    ]

    knowledge_base = models.ForeignKey(
        KnowledgeBase, on_delete=models.CASCADE, related_name="training_jobs"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="PENDING"
    )
    error_message = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
