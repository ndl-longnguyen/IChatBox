from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ai", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AISettings",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("auto_reply_enabled", models.BooleanField(default=False)),
                (
                    "model_name",
                    models.CharField(blank=True, default="", max_length=100),
                ),
                ("language", models.CharField(default="vi", max_length=10)),
                (
                    "system_prompt",
                    models.TextField(
                        default=(
                            "You are a helpful website support assistant. Answer only from "
                            "the provided business knowledge. If the answer is not in the "
                            "knowledge, say you do not have enough information and ask the "
                            "visitor to wait for a human agent."
                        )
                    ),
                ),
                (
                    "max_context_chunks",
                    models.PositiveSmallIntegerField(default=6),
                ),
                ("temperature", models.FloatField(default=0.2)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ai_settings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="knowledgedocument",
            name="content_hash",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="knowledgedocument",
            name="source_file",
            field=models.FileField(
                blank=True, null=True, upload_to="ai_knowledge/"
            ),
        ),
        migrations.CreateModel(
            name="KnowledgeChunk",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("chunk_index", models.PositiveIntegerField()),
                ("content", models.TextField()),
                (
                    "content_hash",
                    models.CharField(db_index=True, max_length=64),
                ),
                ("char_start", models.PositiveIntegerField(default=0)),
                ("char_end", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "document",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chunks",
                        to="ai.knowledgedocument",
                    ),
                ),
            ],
            options={
                "ordering": ["document_id", "chunk_index"],
                "unique_together": {("document", "chunk_index")},
            },
        ),
        migrations.AddIndex(
            model_name="knowledgedocument",
            index=models.Index(
                fields=["status", "language"],
                name="ai_knowledg_status_7569ae_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="knowledgedocument",
            index=models.Index(
                fields=["source", "created_at"],
                name="ai_knowledg_source_9cd31b_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="knowledgechunk",
            index=models.Index(
                fields=["document", "chunk_index"],
                name="ai_knowledg_documen_901c83_idx",
            ),
        ),
    ]
