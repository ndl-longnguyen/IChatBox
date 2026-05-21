from django.conf import settings
from django.db import models


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
    source = models.CharField(max_length=50, default="manual")
    language = models.CharField(max_length=10, default="en")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="DRAFT"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


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
